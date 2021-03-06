import datetime
import os
import time
import cv2
import numpy as np


class LP:
    def __init__(self, path):
        self.args = {"threshold": 0.3, "yolo": path + "/models", "confidence": 0.5}
        self.labels_path = os.path.sep.join([self.args["yolo"], "lp.names"])
        self.LABELS = open(self.labels_path).read().strip().split("\n")
        self.weights_path = os.path.sep.join([self.args["yolo"], "lp.weights"])
        self.config_path = os.path.sep.join([self.args["yolo"], "lp.cfg"])
        self.net = cv2.dnn.readNetFromDarknet(self.config_path, self.weights_path)
        self.colors = np.random.randint(0, 255, size=(len(self.LABELS), 3), dtype="uint8")

    def detect_objects(self, img_cv, image_name):
        image = img_cv
        (H, W) = image.shape[:2]

        ln = self.net.getLayerNames()
        ln = [ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]

        blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (240, 80), swapRB=False, crop=False)
        self.net.setInput(blob)
        
        layer_outputs = self.net.forward(ln)
        idxs, boxes, confidences, class_ids = self.get_data(layer_outputs, self.args, W, H, image, image_name)

        res = []
        if len(idxs) > 0:
            for i in idxs.flatten():
                (x, y) = (boxes[i][0], boxes[i][1])
                start = time.time()
                (w, h) = (boxes[i][2], boxes[i][3])
                start = time.time()
                res.append((self.LABELS[class_ids[i]], confidences[i], (x, y, w, h)))

        return res, idxs, boxes, confidences, class_ids

    def get_data(self, layer_outputs, arguments, W, H, image, image_name):
        boxes = []
        confidences = []
        class_ids = []

        for output in layer_outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > arguments["confidence"]:
                    box = detection[0:4] * np.array([W, H, W, H])
                    (centerX, centerY, width, height) = box.astype("int")
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))
                    h, w, _ = image.shape

                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        idxs = cv2.dnn.NMSBoxes(boxes, confidences, arguments["confidence"], arguments["threshold"])

        return idxs, boxes, confidences, class_ids