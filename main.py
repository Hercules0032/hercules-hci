import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import mysql.connector
import time
import webbrowser

# CONFIGURATION 
pyautogui.FAILSAFE = True
screen_w, screen_h = pyautogui.size()

# Connectting
try:
    db = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="QweAsdZxc123456789",
        database="GestureSystem"
    )
    cursor = db.cursor()
    print("MySQL Backend Live. System Ready.")
except Exception as e:
    print(f"SQL Error: {e}. Check if MySQL is running.")
    db = None


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.8, min_tracking_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

#SYSTEM STATE
cap = cv2.VideoCapture(1) 
plocX, plocY = 0, 0
smoothing = 5
frame_reduction = 120 
last_action_time = 0
prev_y = None

def sql_log(event_name):
    """Helper to log events to MySQL without crashing the loop."""
    if db:
        try:
            sql = "INSERT INTO gesture_logs (gesture_name, confidence_score) VALUES (%s, %s)"
            cursor.execute(sql, (event_name, 0.98))
            db.commit()
            print(f"DB Logged: {event_name}")
        except mysql.connector.Error as err:
            print(f"SQL Log Failed: {err}")

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    frame = cv2.flip(frame, 1)
    h, w, c = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    action_label = "Scanning..."

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            lm = hand_landmarks.landmark
            
            # Key Landmarks
            ix, iy = int(lm[8].x * w), int(lm[8].y * h)
            palm_size = np.linalg.norm(np.array([lm[0].x*w, lm[0].y*h]) - np.array([lm[9].x*w, lm[9].y*h]))

            # Gesture States
            fingers_up = [lm[t].y < lm[t-2].y for t in [8, 12, 16, 20]]
            pinch_dist = np.linalg.norm(np.array([lm[4].x*w, lm[4].y*h]) - np.array([lm[8].x*w, lm[8].y*h]))
            is_pinched = pinch_dist < (palm_size * 0.45)

            #GESTURE HIERARCHY

            # 1. BROWSER (Open Palm)
            if all(fingers_up) and (time.time() - last_action_time) > 3.0:
                action_label = "ACTION: BROWSER"
                webbrowser.open("https://www.google.com")
                sql_log("Open_Browser")
                last_action_time = time.time()

            # 2. VOLUME / CLICK MODE (Is Pinched)
            elif is_pinched:
                # If moving significantly, it's volume
                if prev_y is not None:
                    dy = prev_y - iy
                    if abs(dy) > 15:
                        action_label = "VOLUME CONTROL"
                        if dy > 0: 
                            pyautogui.press("volumeup")
                            sql_log("Vol_Up")
                        else: 
                            pyautogui.press("volumedown")
                            sql_log("Vol_Down")
                        prev_y = iy
                # If static, it's a Click
                elif (time.time() - last_action_time) > 0.8:
                    action_label = "ACTION: CLICK"
                    pyautogui.click()
                    sql_log("Pinch_Click")
                    last_action_time = time.time()
                
                prev_y = iy if prev_y is None else prev_y
                cv2.circle(frame, (ix, iy), 20, (255, 165, 0), cv2.FILLED)

            # 3. NAVIGATION (Index Up)
            elif fingers_up[0] and not any(fingers_up[1:]):
                action_label = "Navigation"
                prev_y = None # Reset volume tracking
                
                # Boundary Clipping for perfect bottom-reach
                curr_x = np.clip(ix, frame_reduction, w - frame_reduction)
                curr_y = np.clip(iy, frame_reduction, h - frame_reduction)
                
                sx = np.interp(curr_x, (frame_reduction, w - frame_reduction), (0, screen_w))
                sy = np.interp(curr_y, (frame_reduction, h - frame_reduction), (0, screen_h))
                
                clocX = plocX + (sx - plocX) / smoothing
                clocY = plocY + (sy - plocY) / smoothing
                
                pyautogui.moveTo(clocX, clocY)
                plocX, plocY = clocX, clocY
            
            else:
                prev_y = None

    
    cv2.rectangle(frame, (frame_reduction, frame_reduction), 
                 (w - frame_reduction, h - frame_reduction), (255, 0, 255), 2)
    cv2.putText(frame, f"Action: {action_label}", (10, 60), 1, 2, (0, 255, 0), 2)
    
    cv2.imshow('Hercules Final Integrated OS', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()
if db: db.close()