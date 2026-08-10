import json
import urllib.request
import urllib.error
import time

def extract_json_from_text(text):
    """
    Strips any leading/trailing markdown characters or extra text 
    to extract only the JSON object between the first '{' and the last '}'.
    """
    text_str = str(text or "").strip()
    start_idx = text_str.find('{')
    end_idx = text_str.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text_str[start_idx:end_idx + 1]
    return text_str

def analyze_email_with_gemini(api_key, email_body, email_subject="", email_sender=""):
    """
    Analyzes the email content using Gemini API via HTTP REST.
    Uses the modern 'gemini-3.5-flash' model which is supported for this API key.
    Includes an automatic retry mechanism for transient server errors (HTTP 503, 500, 429).
    """
    if not api_key:
        raise ValueError("Gemini API Key is missing. Please configure it in Settings.")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    prompt = f"""
    คุณคือผู้ช่วยดึงข้อมูลและสรุปเนื้อหาจากอีเมลภาษาไทยที่มีเนื้อหาขอตรวจประเมินมาตรฐานงานเทคนิคการแพทย์ (LA / Re-LA) 
    วิเคราะห์อีเมลและเอกสารแนบ (โดยเฉพาะแบบฟอร์ม F-7 ใบสมัครขอรับรอง) ต่อไปนี้ แล้วตอบกลับเฉพาะข้อมูล JSON ตามรูปแบบโครงสร้างที่กำหนดเท่านั้น
    
    หัวข้ออีเมล: {email_subject}
    ผู้ส่งอีเมล: {email_sender}
    เนื้อหาอีเมลและเอกสารแนบ F-7:
    {email_body}
    
    โครงสร้าง JSON ที่ต้องการส่งกลับ:
    {{
        "hospital_name": "ชื่อหน่วยงาน/โรงพยาบาล (เช่น เมดไลฟ์ พระรามสาม สหคลินิก)",
        "province": "จังหวัด (เช่น กรุงเทพมหานคร)",
        "evaluation_type": "ประเภทการตรวจ เลือกระหว่าง 'LA' (ขอรับรองใหม่) หรือ 'Re-LA' (ขอรับรองการตรวจประเมินต่อเนื่อง)",
        "application_intent": "ความประสงค์ขอรับรอง เช่น 'ขอรับรองใหม่ (LA)' หรือ 'ขอรับรองการตรวจประเมินต่อเนื่อง (Re-LA)'",
        "passed_la_count": "จำนวนครั้งที่ผ่านการรับรอง LA มาแล้ว (เช่น 'ผ่าน LA มาแล้ว 2 ครั้ง' หรือ '0 ครั้ง')",
        "appointment": "ช่วงวัน/วันหยุด/เดือน ที่ระบุว่าสะดวกให้เข้าตรวจประเมินจากแบบฟอร์ม F-7 (เช่น 'เดือนกรกฎาคม-สิงหาคม 2569' หรือ '14-15 สิงหาคม 2569')",
        "internal_audit_date": "วันที่ตรวจติดตามภายในครั้งล่าสุด (ตามข้อกำหนด MT8) ที่ระบุใน F-7 (เช่น 14 มีนาคม 2569)",
        "internal_audit_warning": "ตรวจสอบความถูกต้อง: หากวันที่ตรวจติดตามภายในเกิน 1 ปีนับจากวันที่ต้องการตรวจประเมิน ให้ขึ้นคำเตือน '⚠️ เกิน 1 ปีนับจากวันที่ขอตรวจ' แต่ถ้าไม่เกิน 1 ปีให้ระบุ '✅ ปกติ (ไม่เกิน 1 ปี)'",
        "mt_info": "สรุปข้อมูลกำลังคนและเตียง เช่น MT X คน ปฏิบัติงาน Y คน Z เตียง W ราย/วัน",
        "contact_name": "ชื่อ-นามสกุลของผู้ประสานงาน/ผู้ติดต่อ (เช่น นางสาวนุชิตา กรมขันธ์)",
        "contact_phone": "เบอร์โทรศัพท์ติดต่อของผู้ประสานงาน (เช่น 0883235195)",
        "address": "ที่อยู่ของหน่วยงานโดยละเอียด",
        "expiry_date": "วันที่ใบอนุญาตเดิมหมดอายุ หรือวัน/เดือน/ปี ที่หมดอายุการรับรองครั้งล่าสุดที่ระบุในแบบฟอร์ม F-7 (เช่น '30 มิถุนายน 2569' หรือหากไม่พบให้ใส่ null)",
        "email": "อีเมลผู้ประสานงาน/หน่วยงาน",
        "hospital_type": "ประเภทหน่วยงาน เลือกหนึ่งอย่างจาก: 'สถานพยาบาลรัฐบาล', 'สถานพยาบาลเอกชน', 'ศูนย์ LAB หรือคลินิก'"
    }}
    """
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    max_retries = 4
    retry_delay = 2.0
    
    for attempt in range(max_retries):
        try:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
            
            with urllib.request.urlopen(req) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                
                # Extract the generated text
                text_response = res_json["candidates"][0]["content"]["parts"][0]["text"]
                
                # Extract the clean JSON substring
                clean_json_str = extract_json_from_text(text_response)
                
                # Parse the text response as JSON
                data = json.loads(clean_json_str)
                
                # Strip string values to clean whitespace
                for key in data:
                    if isinstance(data[key], str):
                        data[key] = data[key].strip()
                return data
                
        except urllib.error.HTTPError as he:
            # 503 (Service Unavailable), 500 (Internal Server Error), 429 (Too Many Requests / Rate limit)
            if he.code in [503, 500, 429] and attempt < max_retries - 1:
                print(f"Gemini API returned transient error HTTP {he.code}. Retrying in {retry_delay}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                # Exponential backoff
                retry_delay *= 1.5
                continue
                
            try:
                err_msg = he.read().decode("utf-8")
                print(f"HTTP Error calling Gemini API: {he.code} - {err_msg}")
            except Exception:
                err_msg = str(he)
            raise Exception(f"Gemini API Error (HTTP {he.code}): โปรดตรวจสอบความถูกต้องของ API Key / สิทธิ์การใช้งานของโปรเจกต์")
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Gemini call encountered unexpected error: {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 1.5
                continue
            print(f"Error calling Gemini REST API: {e}")
            return {
                "hospital_name": "ไม่สามารถวิเคราะห์ได้",
                "province": "",
                "evaluation_type": "LA",
                "mt_info": "",
                "contact_name": "",
                "contact_phone": "",
                "address": "",
                "expiry_date": None,
                "email": "",
                "hospital_type": "สถานพยาบาลรัฐบาล"
            }
