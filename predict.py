from ultralytics import YOLO # type: ignore


def predict_image(image_path: str):
    result_to_client = ""
    model = YOLO("best.pt")
    result = model(image_path)
    predicted_names = [model.names[int(box.cls)] for box in result[0].boxes]
    
    if (predicted_names == []):
        return "ไม่พบอาหารในรูปภาพ"
    elif (predicted_names == ["red_pork_withRice"]):
        result_to_client = "ข้าวหมูเเดง"
    elif (predicted_names == ["greencurry"]):
        result_to_client = "ข้าวแกงเขียวหวาน"
    elif (predicted_names == ["stir_fried_basil"]):
        result_to_client = "ข้าวผัดกะเพรา"

    return result_to_client