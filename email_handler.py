import imaplib
import email
from email.header import decode_header
import os
import shutil
import datetime

TEMP_ATTACH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".streamlit", "temp_attachments")

def parse_email_date_to_yyyy_mm_dd(raw_date_str):
    """
    Parses a raw email date header string to a YYYY-MM-DD string.
    """
    import email.utils
    import datetime
    
    raw_date_str = raw_date_str.strip()
    
    try:
        parsed_tuple = email.utils.parsedate_to_datetime(raw_date_str)
        return parsed_tuple.strftime("%Y-%m-%d")
    except Exception:
        pass
        
    try:
        parsed = email.utils.parsedate(raw_date_str)
        if parsed:
            return f"{parsed[0]:04d}-{parsed[1]:02d}-{parsed[2]:02d}"
    except Exception:
        pass
        
    formats = [
        "%d %b %Y",
        "%d %b %Y %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d/%m/%y"
    ]
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(raw_date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
            
    return datetime.datetime.now().strftime("%Y-%m-%d")

def decode_mime_header(header_value):
    """
    Decodes email headers (like Subject or Sender) that may contain Thai characters or MIME encoding.
    Ensures that TIS-620/Windows-874 headers incorrectly decoded as Latin-1/ISO-8859-1 are repaired.
    """
    if not header_value:
        return ""
    try:
        decoded = decode_header(header_value)
        header_parts = []
        for text, charset in decoded:
            if isinstance(text, bytes):
                decoded_text = None
                charsets_to_try = []
                if charset:
                    charsets_to_try.append(charset)
                charsets_to_try.extend(["utf-8", "tis-620", "windows-874", "iso-8859-1"])
                
                for c in charsets_to_try:
                    try:
                        decoded_text = text.decode(c)
                        # If decoded as Latin-1/ISO-8859-1, check if it's actually TIS-620/Windows-874
                        if c.lower() in ["iso-8859-1", "latin-1", "latin1"]:
                            try:
                                raw_bytes = decoded_text.encode("latin1")
                                for alt_c in ["utf-8", "tis-620", "windows-874"]:
                                    try:
                                        test_decode = raw_bytes.decode(alt_c)
                                        if any(0x0E00 <= ord(char) <= 0x0E7F for char in test_decode):
                                            decoded_text = test_decode
                                            break
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        break
                    except Exception:
                        pass
                if decoded_text is None:
                    decoded_text = text.decode("utf-8", errors="ignore")
                header_parts.append(decoded_text)
            else:
                s = str(text)
                # If s has characters in the Latin-1 range (161 to 255), they might be TIS-620 bytes
                if any(161 <= ord(char) <= 255 for char in s):
                    try:
                        raw_bytes = s.encode("latin1")
                        for alt_c in ["tis-620", "windows-874", "utf-8"]:
                            try:
                                test_decode = raw_bytes.decode(alt_c)
                                if any(0x0E00 <= ord(char) <= 0x0E7F for char in test_decode):
                                    s = test_decode
                                    break
                            except Exception:
                                pass
                    except Exception:
                        pass
                header_parts.append(s)
        return "".join(header_parts)
    except Exception as e:
        print(f"Error decoding header: {e}")
        return str(header_value)

def get_email_body(msg):
    """
    Extracts plain text body from a MIME email message.
    """
    body_text = ""
    html_fallback = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if content_type == "text/plain" and "attachment" not in content_disposition:
                charset = part.get_content_charset() or "utf-8"
                try:
                    body_text += part.get_payload(decode=True).decode(charset, errors="ignore") + "\n"
                except Exception:
                    pass
            elif content_type == "text/html" and "attachment" not in content_disposition:
                charset = part.get_content_charset() or "utf-8"
                try:
                    html_fallback += part.get_payload(decode=True).decode(charset, errors="ignore") + "\n"
                except Exception:
                    pass
    else:
        content_type = msg.get_content_type()
        charset = msg.get_content_charset() or "utf-8"
        if content_type in ["text/plain", "text/html"]:
            try:
                body_text = msg.get_payload(decode=True).decode(charset, errors="ignore")
            except Exception:
                pass
                
    final_body = body_text.strip() if body_text.strip() else html_fallback.strip()
    return final_body

def save_email_attachments(msg, mail_id):
    """
    Saves attachments to a temporary directory with maximum robustness.
    Works for all attachment types including standard, inline, and custom header definitions.
    """
    temp_dir = os.path.join(TEMP_ATTACH_DIR, str(mail_id))
    os.makedirs(temp_dir, exist_ok=True)
    saved_files = []
    import re
    
    # msg.walk() yields the message itself if not multipart, or all parts if multipart
    for part in msg.walk():
        # Try retrieving filename from all possible headers
        filename = part.get_filename()
        if not filename:
            filename = part.get_param("name")
        if not filename:
            filename = part.get_param("filename")
            
        if filename:
            filename = decode_mime_header(filename)
            
            # Clean up newlines, carriage returns, and tabs that arise from MIME header folding
            filename = filename.replace("\r", "").replace("\n", "").replace("\t", "")
            filename = " ".join(filename.split())
            
            # Remove characters that are invalid in Windows filenames
            filename = re.sub(r'[\\/*?:"<>|]', "", filename)
            filename = os.path.basename(filename)
            
            # Ensure filename is not empty after sanitization
            if not filename:
                filename = f"unnamed_attachment_{len(saved_files) + 1}"
                
            # Prevent files from overwriting each other if they share the same name
            name, ext = os.path.splitext(filename)
            counter = 1
            unique_filename = filename
            while unique_filename in saved_files:
                unique_filename = f"{name}_{counter}{ext}"
                counter += 1
                
            filename = unique_filename
            filepath = os.path.join(temp_dir, filename)
            
            try:
                payload = part.get_payload(decode=True)
                if payload:
                    with open(filepath, "wb") as f:
                        f.write(payload)
                    saved_files.append(filename)
            except Exception as e:
                print(f"Error saving attachment {filename}: {e}")
                
    # Detect Cloud Drive URLs (Google Drive, Dropbox, OneDrive) in email body
    try:
        body_text = get_email_body(msg)
        if body_text:
            cloud_urls = re.findall(r'https?://[^\s<>"]*(?:drive\.google\.com|dropbox\.com|1drv\.ms|onedrive)[^\s<>"]*', body_text)
            for c_idx, url in enumerate(cloud_urls):
                shortcut_filename = f"ลิงก์เอกสาร_Cloud_Drive_{c_idx+1}.url"
                shortcut_filename = os.path.basename(shortcut_filename)
                shortcut_path = os.path.join(temp_dir, shortcut_filename)
                
                shortcut_content = f"[InternetShortcut]\nURL={url}\n"
                with open(shortcut_path, "w", encoding="utf-8") as f:
                    f.write(shortcut_content)
                if shortcut_filename not in saved_files:
                    saved_files.append(shortcut_filename)
    except Exception as e:
        print(f"Error extracting cloud links: {e}")
                
    if not saved_files:
        try:
            os.rmdir(temp_dir)
        except Exception:
            pass
        return None
        
    return temp_dir

def fetch_emails_by_range(imap_server, email_addr, password, subject_keywords=None, days_limit=7, max_emails=None):
    """
    Connects to IMAP server and fetches emails matching date range and keywords.
    Supported days_limit values: 7 (Last 7 Days), 30 (Last 30 Days), 0 (All Unread).
    If max_emails is specified, stops fetching once that number of matched emails is processed.
    """
    if subject_keywords is None:
        subject_keywords = ["la", "ตรวจประเมิน"]
        
    # Clean up old temp attachments
    if os.path.exists(TEMP_ATTACH_DIR):
        try:
            shutil.rmtree(TEMP_ATTACH_DIR)
        except Exception as e:
            print(f"Error cleaning temp attachment directory: {e}")
            
    print(f"Connecting to {imap_server}...")
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(email_addr, password)
    
    mail.select("inbox")
    
    # Construct IMAP Search Query based on date range
    if days_limit > 0:
        date_ago = datetime.date.today() - datetime.timedelta(days=days_limit)
        since_date_str = date_ago.strftime("%d-%b-%Y") # e.g. 09-Jul-2026
        search_query = f'(SINCE "{since_date_str}")'
    else:
        # 0 means fetch all unread emails
        search_query = "UNSEEN"
        
    print(f"Searching mail inbox with query: {search_query}")
    status, messages = mail.search(None, search_query)
    
    email_list = []
    if status != "OK":
        mail.close()
        mail.logout()
        return email_list
        
    mail_ids = messages[0].split()
    print(f"Found {len(mail_ids)} matching emails in range. Processing...")
    
    # We loop backwards (newest emails first)
    for mail_id in reversed(mail_ids):
        # Fetch both FLAGS and raw RFC822 email content
        status, data = mail.fetch(mail_id, "(FLAGS RFC822)")
        if status != "OK" or not data:
            continue
            
        # Parse flags
        flags_part = data[0][0]
        is_seen = b'\\Seen' in flags_part
        status_label = "อ่านแล้ว" if is_seen else "ใหม่ (ยังไม่ได้อ่าน)"
        
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        subject = decode_mime_header(msg["Subject"])
        sender = decode_mime_header(msg["From"])
        date_str = msg["Date"]
        
        # Filter subject by keywords (case-insensitive)
        if not subject_keywords:
            matched = True
        else:
            matched = False
            subject_lower = subject.lower()
            for kw in subject_keywords:
                if kw.lower() in subject_lower:
                    matched = True
                    break
                
        if matched:
            body = get_email_body(msg)
            if date_str:
                body = f"{body}\n\n--- วันที่ได้รับอีเมล: {date_str} ---"
            mail_id_str = mail_id.decode("utf-8")
            temp_dir = save_email_attachments(msg, mail_id_str)
            if not temp_dir:
                temp_dir = os.path.join(TEMP_ATTACH_DIR, mail_id_str)
                os.makedirs(temp_dir, exist_ok=True)
            
            # Auto-sweep all past thread attachments across the entire inbox for this conversation thread
            try:
                import app
                base_subj = app.clean_base_subject(subject)
                h_name = app.extract_hospital_name(subject, body)
                
                if base_subj or (h_name and h_name != "ไม่พบชื่อโรงพยาบาล"):
                    status_all, data_all = mail.search(None, "ALL")
                    all_inbox_ids = data_all[0].split() if status_all == "OK" else mail_ids
                    for t_id in all_inbox_ids:
                        if t_id == mail_id:
                            continue
                        res_t, data_t = mail.fetch(t_id, "(BODY[HEADER.FIELDS (SUBJECT FROM)])")
                        if res_t == "OK" and data_t:
                            hdr_t = email.message_from_bytes(data_t[0][1])
                            sub_t = decode_mime_header(hdr_t.get("Subject", ""))
                            if app.clean_base_subject(sub_t) == base_subj or (h_name and h_name != "ไม่พบชื่อโรงพยาบาล" and app.extract_hospital_name(sub_t, "") == h_name):
                                res_f, data_f = mail.fetch(t_id, "(RFC822)")
                                if res_f == "OK" and data_f:
                                    t_msg = email.message_from_bytes(data_f[0][1])
                                    t_temp = save_email_attachments(t_msg, f"thread_sub_{t_id.decode('utf-8')}")
                                    if t_temp and os.path.exists(t_temp):
                                        for f in os.listdir(t_temp):
                                            src = os.path.join(t_temp, f)
                                            dst = os.path.join(temp_dir, f)
                                            if not os.path.exists(dst):
                                                shutil.copy2(src, dst)
            except Exception as t_err:
                print(f"Thread Sweep fetch error: {t_err}")
            
            # Check completeness of attachments
            filenames = []
            if temp_dir and os.path.exists(temp_dir):
                filenames = os.listdir(temp_dir)
            completeness = check_attachments_completeness(filenames)
            
            email_list.append({
                "id": mail_id_str,
                "subject": subject,
                "sender": sender,
                "date": date_str,
                "body": body,
                "temp_dir": temp_dir,
                "status": status_label,
                "completeness": completeness
            })
            
            if max_emails and len(email_list) >= max_emails:
                break
                
    mail.close()
    mail.logout()
    
    return email_list

def check_attachments_completeness(filenames):
    """
    Checks if the 9 target files for LA audit are present in the list of filenames
    using flexible pattern-based matching and runs deep version checking.
    """
    patterns = {
        1: lambda f: "qm-lab-001" in f or "คู่มือคุณภาพ" in f,
        2: lambda f: "f12" in f or "checklist-mt2565" in f,
        3: lambda f: "ha service profile" in f or "service_profile" in f or "service profile" in f,
        4: lambda f: "f1" in f and ("lab_profile" in f or "lab profile" in f),
        5: lambda f: "f7" in f or "application_form" in f or "application form" in f or "ใบสมัคร" in f,
        6: lambda f: "รายชื่อเจ้าหน้าที่" in f or "รายชื่อเจ้าหน้าที่" in f or "รายชื่อ" in f,
        7: lambda f: "lab_safety" in f or "safety_checklist" in f or "safety" in f or "ความปลอดภัย" in f,
        8: lambda f: "qp-lab-001" in f or "คู่มือห้องปฏิบัติการ" in f,
        9: lambda f: "fm-lab-043" in f or "บัญชีรายชื่อเอกสาร" in f or "master document" in f
    }
    
    found_map = {i: False for i in range(1, 10)}
    found_files = {i: "" for i in range(1, 10)}
    
    for filename in filenames:
        f_lower = filename.lower()
        for i, match_fn in patterns.items():
            if not found_map[i] and match_fn(f_lower):
                found_map[i] = True
                found_files[i] = filename
                break # Move to next filename once matched
                
    missing = [i for i, found in found_map.items() if not found]
    complete = len(missing) == 0
    
    # Run version checking for found files
    versions = {}
    versions_ok = {}
    
    for i in range(1, 10):
        if not found_map[i]:
            versions[i] = "❌ ไม่พบไฟล์เอกสาร"
            versions_ok[i] = False
            continue
            
        filename = found_files[i]
        f_lower = filename.lower()
        
        if i == 1: # QM-LAB-001
            # Check for version date, e.g. 20260501
            if "20260501" in f_lower or "2026" in f_lower:
                versions[i] = "✅ เวอร์ชันถูกต้อง (_20260501)"
                versions_ok[i] = True
            else:
                versions[i] = "⚠️ ควรตรวจสอบเวอร์ชัน (ควรเป็นฉบับวันที่ 20260501 หรือใหม่กว่า)"
                versions_ok[i] = False
                
        elif i == 2: # F12 Checklist 2565
            # Must be V.4 or Version 4
            if "v.4" in f_lower or "v4" in f_lower or "version 4" in f_lower or "version4" in f_lower:
                versions[i] = "✅ F12 checklist 2565 เวอร์ชันล่าสุด (V.4)"
                versions_ok[i] = True
            else:
                versions[i] = "⚠️ F12 checklist 2565 ไม่ใช่เวอร์ชันล่าสุด (พบ V.3 หรือเก่ากว่า, ควรเป็น V.4)"
                versions_ok[i] = False
                
        elif i == 5: # F7 Application Form
            # Must be update 5-2-67 (or 2567 onwards) and signed
            is_signed = "signed" in f_lower or "ลงนาม" in f_lower or "เขียนแล้ว" in f_lower or "สแกน" in f_lower or "ตรวจแล้ว" in f_lower
            is_correct_version = "5-2-67" in f_lower or "5-2-2567" in f_lower or "5ก.พ.67" in f_lower or "5 ก.พ. 67" in f_lower or "67" in f_lower or "68" in f_lower or "69" in f_lower
            
            if is_correct_version and is_signed:
                versions[i] = "✅ F7 ใบสมัครเวอร์ชันถูกต้อง (5-2-67) และมีการลงนามแล้ว"
                versions_ok[i] = True
            elif is_correct_version and not is_signed:
                versions[i] = "⚠️ F7 ใบสมัครเวอร์ชันถูกต้องแต่ไม่พบคำว่า signed/ลงนามในชื่อไฟล์"
                versions_ok[i] = False
            elif not is_correct_version and is_signed:
                versions[i] = "⚠️ F7 ใบสมัครมีการลงนามแต่ไม่ใช่เวอร์ชันล่าสุด (ควรเป็นฉบับปรับปรุง 5-2-67)"
                versions_ok[i] = False
            else:
                versions[i] = "⚠️ F7 ใบสมัครไม่ใช่เวอร์ชันล่าสุด (ควรใช้ 5-2-67) และไม่พบการลงนาม"
                versions_ok[i] = False
                
        elif i == 7: # LAB_SAFETY_Checklist 2565
            # Must be Version 2
            if "version 2" in f_lower or "version2" in f_lower or "v.2" in f_lower or "v2" in f_lower:
                versions[i] = "✅ LAB SAFETY checklist 2565 เวอร์ชันล่าสุด (Version 2)"
                versions_ok[i] = True
            else:
                versions[i] = "⚠️ LAB SAFETY checklist 2565 ไม่ใช่เวอร์ชันล่าสุด (พบ Version 1, ควรเป็น Version 2)"
                versions_ok[i] = False
                
        else:
            # Other files are correct if found
            versions[i] = "✅ พบไฟล์และชื่อถูกต้อง"
            versions_ok[i] = True
            
    if complete:
        status_text = "เอกสารครบถ้วน (9/9)"
    else:
        missing_str = ", ".join(str(m) for m in missing)
        status_text = f"ขาดไฟล์ที่: {missing_str}"
        
    return {
        "complete": complete,
        "found_count": 9 - len(missing),
        "status_text": status_text,
        "missing_indices": missing,
        "found_map": found_map,
        "found_files": found_files,
        "versions": versions,
        "versions_ok": versions_ok
    }

def extract_text_from_pdf(pdf_path):
    """
    Extracts text content from the first 5 pages of a PDF file using pypdf.
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        text = []
        # Extract from first 5 pages to avoid token overload
        for i in range(min(5, len(reader.pages))):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text.append(page_text)
        return "\n".join(text)
    except Exception as e:
        print(f"Error extracting PDF text from {pdf_path}: {e}")
        return ""

def check_folder_completeness(folder_path):
    """
    Scans all files inside a hospital folder (including accumulated multi-round attachments)
    and checks completeness for the 9 LA target documents.
    """
    if not folder_path or not os.path.exists(folder_path):
        return {
            "complete": False,
            "found_count": 0,
            "status_text": "ไม่พบโฟลเดอร์เอกสาร",
            "missing_indices": list(range(1, 10)),
            "found_map": {i: False for i in range(1, 10)},
            "found_files": {i: "" for i in range(1, 10)},
            "versions": {i: "❌ ไม่พบไฟล์เอกสาร" for i in range(1, 10)},
            "versions_ok": {i: False for i in range(1, 10)}
        }
        
    filenames = []
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            filenames.append(f)
            
    return check_attachments_completeness(filenames)
def sweep_thread_attachments_imap(target_email, config):
    """
    Connects to IMAP and sweeps ALL messages across the whole inbox that belong to the same
    conversation thread (by matching clean base_subject or hospital_name), recovering 100% of
    attachments across all past forward/reply iterations.
    """
    server = config.get("imap_server", "imap.gmail.com")
    port = int(config.get("imap_port", 993))
    email_user = config.get("email")
    password = config.get("password")
    
    if not email_user or not password:
        return None
        
    try:
        import app
        base_subj = app.clean_base_subject(target_email.get("subject", ""))
        h_name = app.extract_hospital_name(target_email.get("subject", ""), target_email.get("body", ""))
        
        mail = connect_imap(server, port, email_user, password)
        status, data = mail.search(None, "ALL")
        if status != "OK":
            mail.logout()
            return None
            
        msg_nums = data[0].split()
        matching_uids = []
        
        for num in msg_nums:
            res, msg_data = mail.fetch(num, "(BODY[HEADER.FIELDS (SUBJECT FROM DATE IN-REPLY-TO REFERENCES)])")
            if res == "OK":
                header_bytes = msg_data[0][1]
                msg = email.message_from_bytes(header_bytes)
                subj = decode_mime_header(msg.get("Subject", ""))
                curr_base = app.clean_base_subject(subj)
                
                if curr_base and curr_base == base_subj:
                    matching_uids.append(num.decode('utf-8'))
                elif h_name and h_name != "ไม่พบชื่อโรงพยาบาล":
                    curr_h = app.extract_hospital_name(subj, "")
                    if curr_h == h_name:
                        matching_uids.append(num.decode('utf-8'))

        swept_dir = os.path.join(TEMP_ATTACH_DIR, f"thread_sweep_{target_email.get('id', '0')}")
        os.makedirs(swept_dir, exist_ok=True)
        
        for uid in matching_uids:
            res, full_data = mail.fetch(uid, "(RFC822)")
            if res == "OK":
                full_msg = email.message_from_bytes(full_data[0][1])
                sub_temp = save_email_attachments(full_msg, f"sweep_sub_{uid}")
                if sub_temp and os.path.exists(sub_temp):
                    for f in os.listdir(sub_temp):
                        src = os.path.join(sub_temp, f)
                        dst = os.path.join(swept_dir, f)
                        if not os.path.exists(dst):
                            import shutil
                            shutil.copy2(src, dst)
                            
        mail.close()
        mail.logout()
        return swept_dir
    except Exception as e:
        print(f"Error in sweep_thread_attachments_imap: {e}")
        return None
