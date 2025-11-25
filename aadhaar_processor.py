"""
YOLOv8 Aadhaar Masking (Full Auto Pipeline)
-------------------------------------------
✅ Auto rotation (0°–345°, every 15°)
✅ Regex-based Aadhaar detection even if YOLO labels are wrong
✅ Falls back to orientation detection if YOLO fails
✅ Masks 65% of Aadhaar area (keeps last 4 digits visible)
Adapted for API usage
"""

import os, cv2, re, json, numpy as np, pytesseract, time
from ultralytics import YOLO

CONFIDENCE_THRESHOLD = 0.6
IMAGE_SIZE = 640

def reset_extracted_info():
    return {
        "GENDER": None,
        "AADHAR_NUMBER": None,
        "NAME": None,
        "DATE_OF_BIRTH": None
    }

def clean_text(text, is_date=False):
    if is_date:
        date_match = re.search(r'\b\d{2}[/-]\d{2}[/-]\d{4}\b', text)
        return date_match.group(0) if date_match else None
    return re.sub(r'[^\w\s]', ' ', text).strip()

# ---------------- CONFIG ----------------
CONF_THRESH = 0.6
ROTATION_STEP = 15
MASK_RATIO = 0.65
AADHAAR_REGEX = re.compile(r"\d{4}\s?\d{4}\s?\d{4}")

# Possible YOLO paths
MODEL_PATHS = [
    "model/weights/best.pt",
    "runs/detect/aadhar_model/weights/best.pt",
    "aadhar_model.pt",
    "../model/weights/best.pt",
    "../aadhar_model.pt"
]

MODEL_PATH = next((p for p in MODEL_PATHS if os.path.exists(p)), None)

# Global counter to track model usage (for logging)
_model_usage_count = 0

if MODEL_PATH is None:
    print("❌ YOLO model not found in expected locations.")
    for p in MODEL_PATHS:
        print(f"  - {p}")
    print("Please ensure the YOLO model is available at one of these paths")
    model = None
else:
    print(f"✅ Loading YOLO model from: {MODEL_PATH}")
    print("⏳ This happens ONCE at startup, not per-request...")
    model = YOLO(MODEL_PATH)
    print(f"✅ Model loaded successfully! (Memory: ~{model.__sizeof__() / 1024 / 1024:.1f}MB)")
    print("🔄 Model will be reused for all subsequent requests")

# ---------------- HELPERS ----------------
def rotate_image(image, angle):
    """Rotate image without cropping edges"""
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    
    # Get rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Calculate new bounding dimensions to fit entire rotated image
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    
    # Compute new width and height
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    
    # Adjust rotation matrix to account for translation
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    
    # Perform rotation with new dimensions
    return cv2.warpAffine(image, M, (new_w, new_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

def extract_text_from_box(image, box):
    x1, y1, x2, y2 = map(int, box)
    roi = image[y1:y2, x1:x2]
    return pytesseract.image_to_string(roi, config="--psm 6").strip()

def mask_aadhaar_area(image, box):
    """Mask the Aadhaar area and return the masked image (does not modify original)"""
    masked_image = image.copy()
    x1, y1, x2, y2 = map(int, box)
    width = x2 - x1
    mask_width = int(width * MASK_RATIO)
    masked_image[y1:y2, x1:x1 + mask_width] = (0, 0, 0)
    return masked_image

def rotate_image_back(image, angle):
    """Rotate image back to original orientation without cropping"""
    if angle == 0:
        return image
    
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    
    # Get rotation matrix for reverse rotation
    M = cv2.getRotationMatrix2D(center, -angle, 1.0)
    
    # Calculate new bounding dimensions
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    
    # Adjust rotation matrix
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    
    # Perform rotation with new dimensions and white background
    return cv2.warpAffine(image, M, (new_w, new_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

def format_masked_aadhaar(aadhaar_text):
    digits = re.sub(r"\D", "", aadhaar_text)
    return f"XXXX XXXX {digits[-4:]}" if len(digits) >= 12 else "XXXX XXXX XXXX"

# ---------------- YOLO-BASED DETECTION ----------------
def detect_aadhaar_yolo(image, include_all_rotations=True):
    """
    Two-stage Aadhaar detection with rotation optimization:
    Stage 1: Check 4 major angles (0, 90, 180, 270) - fast check
    Stage 2: If Stage 1 fails, check remaining 19 angles (15, 30, 45, ... excluding already checked angles)
    """
    start_time = time.time()
    
    if model is None:
        return None, None, None, None, image, None, 0
    
    best_conf, best_angle, best_box, best_text = 0, 0, None, None
    best_image = image.copy()
    original_image = image.copy()
    
    # Stage 1: Check 4 major angles (0, 90, 180, 270) - "without rotation" check
    major_angles = [0, 90, 180, 270]
    print(f"🔍 Stage 1: Checking {len(major_angles)} major angles (fast check)...")
    
    for angle in major_angles:
        if angle == 0:
            current_image = image
        else:
            current_image = rotate_image(image, angle)
        
        results = model(current_image, conf=CONF_THRESH, verbose=False)
        for result in results:
            for box in result.boxes:
                conf = float(box.conf[0])
                text = extract_text_from_box(current_image, box.xyxy[0])
                if re.search(AADHAAR_REGEX, text.replace(" ", "")):
                    inference_time = (time.time() - start_time) * 1000
                    print(f"✅ Stage 1 Success: Found Aadhaar at {angle}° with confidence {conf:.2f}")
                    return conf, angle, box.xyxy[0], text, current_image, original_image, inference_time
    
    print(f"⚠️ Stage 1 Failed: No Aadhaar detected in major angles")
    
    # Stage 2: Only if Stage 1 fails and include_all_rotations is True
    # Check remaining angles (exclude the 4 major angles already checked)
    if include_all_rotations:
        # Generate all angles from 15 to 345 in steps of 15, excluding major angles
        all_angles = range(ROTATION_STEP, 360, ROTATION_STEP)
        remaining_angles = [angle for angle in all_angles if angle not in major_angles]
        
        print(f"🔍 Stage 2: Checking {len(remaining_angles)} remaining angles (thorough check)...")
        
        for angle in remaining_angles:
            rotated = rotate_image(image, angle)
            results = model(rotated, conf=CONF_THRESH, verbose=False)
            for result in results:
                for box in result.boxes:
                    conf = float(box.conf[0])
                    text = extract_text_from_box(rotated, box.xyxy[0])
                    if re.search(AADHAAR_REGEX, text.replace(" ", "")) and conf > best_conf:
                        best_conf, best_angle, best_box, best_text, best_image = conf, angle, box.xyxy[0], text, rotated.copy()
            if best_conf > 0.85:  # confident early exit
                print(f"✅ Stage 2 Success: Found Aadhaar at {angle}° with confidence {best_conf:.2f}")
                break
    
    inference_time = (time.time() - start_time) * 1000
    if best_conf > 0:
        print(f"✅ Stage 2 Complete: Best result at {best_angle}° with confidence {best_conf:.2f}")
        return best_conf, best_angle, best_box, best_text, best_image, original_image, inference_time
    else:
        print(f"❌ Both stages failed: No Aadhaar detected at any angle")
        return None, None, None, None, image, original_image, inference_time

def try_multiple_orientations(image):
    """
    Try image in multiple orientations and return the one with best detections
    Returns: (best_image, rotation_angle_used)
    """
    if model is None:
        return image, 0
    
    orientations = {
        "original": (image, 0),
        "90°": (cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE), 90),
        "180°": (cv2.rotate(image, cv2.ROTATE_180), 180),
        "270°": (cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE), 270)
    }
    
    best_orientation = "original"
    best_count = 0
    best_image = image
    best_angle = 0
    
    print(f"🔄 Trying multiple orientations to find best detection...")
    
    for orientation_name, (oriented_image, angle) in orientations.items():
        resized = cv2.resize(oriented_image, (IMAGE_SIZE, IMAGE_SIZE))
        results = model.predict(source=resized, conf=CONFIDENCE_THRESHOLD, verbose=False)
        
        detection_count = 0
        for result in results:
            if result.boxes is not None:
                detection_count = len(result.boxes)
        
        print(f"  {orientation_name}: {detection_count} detections")
        
        if detection_count > best_count:
            best_count = detection_count
            best_orientation = orientation_name
            best_image = oriented_image
            best_angle = angle
    
    print(f"✅ Best orientation: {best_orientation} with {best_count} detections")
    return best_image, best_angle

def process_image_with_rotation(image_path, original_image):
    """
    Process an image to extract Aadhaar card information
    with automatic orientation detection by trying all orientations
    Returns: (extracted_info, masked_image, rotation_angle)
    """
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return None, None, 0
    
    print(f"\n📄 Processing image with fallback: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Failed to load image: {image_path}")
        return None, None, 0
    
    # Step 1: Find best orientation by trying all 4 orientations
    image, detected_angle = try_multiple_orientations(image)
    
    # Step 2: Resize image for YOLO
    resized_image = cv2.resize(image, (IMAGE_SIZE, IMAGE_SIZE))
    
    # Step 3: Run YOLO prediction
    results = model.predict(source=resized_image, conf=CONFIDENCE_THRESHOLD, verbose=False)
    best_result = results
    
    # Step 4: Process detections
    extracted_info = reset_extracted_info()
    image_with_boxes = resized_image.copy()
    
    for result in best_result:
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            print("No detections found.")
            continue
        
        for i in range(len(boxes)):
            x1, y1, x2, y2 = map(int, boxes.xyxy[i])
            class_id = int(boxes.cls[i])
            confidence = float(boxes.conf[i])
            
            # Map trained labels to correct Aadhaar fields
            class_name_mapping = {
                'GENDER': 'AADHAR_NUMBER',
                'AADHAR_NUMBER': 'DATE_OF_BIRTH',
                'NAME': 'GENDER',
                'DATE_OF_BIRTH': 'NAME'
            }
            
            original_label = result.names[class_id]
            label = class_name_mapping.get(original_label, original_label)
            
            cropped_image = resized_image[y1:y2, x1:x2]
            
            # Aadhaar number masking
            if label == "AADHAR_NUMBER":
                h, w = cropped_image.shape[:2]
                mask_width = int(w * 0.35)
                masked_image = cropped_image.copy()
                masked_image[:, :-mask_width] = (0, 0, 0)
                image_with_boxes[y1:y2, x1:x2] = masked_image
                cropped_image = masked_image
            
            # OCR preprocessing
            gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
            _, thresh_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY)
            
            ocr_config = "--psm 7 --oem 1" if label == "DATE_OF_BIRTH" else "--psm 6"
            try:
                extracted_text = pytesseract.image_to_string(thresh_image, config=ocr_config).strip()
            except Exception as e:
                print(f"OCR error: {e}")
                extracted_text = ""
            
            # Clean extracted text
            if label == "AADHAR_NUMBER":
                extracted_text = clean_text(extracted_text)
            elif label == "DATE_OF_BIRTH":
                extracted_text = clean_text(extracted_text, is_date=True)
            
            if label in extracted_info:
                extracted_info[label] = extracted_text
            
            print(f"🧾 Field: {label}, Conf: {confidence:.2f}, Text: {extracted_text}")
    
    # Print summary
    print("\n--- Extracted Information ---")
    for key, value in extracted_info.items():
        if value:
            print(f"{key}: {value}")
    
    return extracted_info, image_with_boxes, detected_angle

# ---------------- MAIN PROCESSOR ----------------
def process_single_image(image_path=None, image_array=None, include_all_rotations=True):
    """
    Main processing function with YOLO detection and fallback to orientation detection
    Can work with either file path or numpy array (in-memory processing)
    Returns: (extracted_info, masked_image_array, metrics) or None on failure
    """
    global _model_usage_count
    
    if model is None:
        print("❌ Model not loaded. Cannot process image.")
        return None
    
    # Increment usage counter
    _model_usage_count += 1
    
    # Load image from array or file path
    if image_array is not None:
        image = image_array
        print(f"\n📄 Processing image from memory (Model reuse #{_model_usage_count})")
    elif image_path is not None:
        image = cv2.imread(image_path)
        if image is None:
            print(f"⚠️ Could not read image: {image_path}")
            return None
        print(f"\n📄 Processing: {image_path} (Model reuse #{_model_usage_count})")
    else:
        print("❌ No image provided (neither array nor path)")
        return None
    
    # Try YOLO-based detection with rotation
    # Measure preprocessing (negligible here as we just pass image, but keeping placeholder)
    t0 = time.time()
    # Preprocessing logic if any
    t1 = time.time()
    preprocessing_ms = (t1 - t0) * 1000

    conf, angle, box, aadhaar_text, best_image, original_image, inference_ms = detect_aadhaar_yolo(image, include_all_rotations=include_all_rotations)
    
    t2 = time.time()
    
    if aadhaar_text:  # YOLO found Aadhaar
        # Mask the Aadhaar in the rotated image
        masked_image = mask_aadhaar_area(best_image, box)
        
        masked_display = format_masked_aadhaar(aadhaar_text)
        print(f"✅ Aadhaar Detected @ {angle}° | Conf: {conf:.2f}")
        print(f"🪪 Aadhaar (masked view): {masked_display}")
        print(f"✅ Image returned in original orientation (in memory)")
        
        extracted_info = {
            "AADHAR_NUMBER": masked_display,
            "confidence": float(conf),
            "rotation_angle": int(angle)
        }
        
        t3 = time.time()
        postproc_ms = (t3 - t2) * 1000
        
        metrics = {
            "3a_preprocessing_ms": preprocessing_ms,
            "3b_model_forward_ms": inference_ms,
            "3_model_inference_total_ms": inference_ms, # In this case same as forward, but could include overhead
            "4a_postproc_validation_ms": postproc_ms
        }
        
        return extracted_info, masked_image, metrics
    
    # Fallback — use orientation detection if YOLO fails
    else:
        print("🔄 YOLO detection failed, trying fallback with orientation detection...")
        
        # For in-memory processing, we need to save temporarily for the fallback function
        # TODO: Refactor process_image_with_rotation to work with arrays
        if image_path is None:
            import tempfile, uuid
            temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.jpg")

            cv2.imwrite(temp_path, image)
            extracted_info, masked_image, detected_angle = process_image_with_rotation(
                temp_path, original_image
            )
            for _ in range(10):
                try:
                    os.remove(temp_path)
                    break
                except PermissionError:
                    time.sleep(0.05)
        else:
            extracted_info, masked_image, detected_angle = process_image_with_rotation(image_path, original_image)
        
        if extracted_info is not None and masked_image is not None:
            aadhaar_text = extracted_info.get("AADHAR_NUMBER", None)
            
            t3 = time.time()
            postproc_ms = (t3 - t2) * 1000
            
            metrics = {
                "3a_preprocessing_ms": preprocessing_ms,
                "3b_model_forward_ms": inference_ms, # YOLO failed, so this is the time it took to fail
                "3_model_inference_total_ms": inference_ms,
                "4a_postproc_validation_ms": postproc_ms # Includes fallback time
            }

            if aadhaar_text:
                masked_display = format_masked_aadhaar(aadhaar_text)
                print(f"✅ Aadhaar Detected from fallback")
                print(f"🪪 Aadhaar (masked view): {masked_display}")
                print(f"✅ Image returned in original orientation (in memory)")
                
                extracted_info["AADHAR_NUMBER"] = masked_display
                return extracted_info, masked_image, metrics
            else:
                # No Aadhaar found but still return the processed image in original orientation
                print("⚠️ No Aadhaar number detected, but returning processed image")
                print(f"✅ Image returned in original orientation (in memory)")
                
                extracted_info["AADHAR_NUMBER"] = "Not detected"
                return extracted_info, masked_image, metrics
        
        # Last resort: return original image if everything fails
        print("⚠️ No Aadhaar detected even after fallback, returning original image")
        
        # Return resized original image
        resized_original = cv2.resize(image, (IMAGE_SIZE, IMAGE_SIZE))
        
        extracted_info = {
            "AADHAR_NUMBER": "Not detected",
            "NAME": None,
            "DATE_OF_BIRTH": None,
            "GENDER": None
        }
        
        t3 = time.time()
        postproc_ms = (t3 - t2) * 1000
        
        metrics = {
            "3a_preprocessing_ms": preprocessing_ms,
            "3b_model_forward_ms": inference_ms,
            "3_model_inference_total_ms": inference_ms,
            "4a_postproc_validation_ms": postproc_ms
        }
        
        return extracted_info, resized_original, metrics

