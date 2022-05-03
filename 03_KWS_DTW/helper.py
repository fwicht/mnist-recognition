from svgpathtools import svg2paths, paths2svg, Path
import numpy as np
from PIL import Image, ImageDraw
from skimage.filters import threshold_otsu as otsu
import cv2
import os


class Slicer:
    def __init__(self, images: tuple, frames: tuple) -> None:
        self.images = self.__fileList(images[0], images[1])
        self.frames = self.__fileList(frames[0], frames[1])
        assert(len(self.images) == len(self.frames)
               ), f"Number of images {len(self.images)} and frames {len(self.frames)} must be equal"
        self.documents = [cv2.imread(image, cv2.IMREAD_GRAYSCALE)
                          for image in self.images]

    def __fileList(self, path: str, ext: str) -> list:
        matches = []
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith((ext)):
                    matches.append(os.path.join(root, filename))
        return matches

    def __get_frame(self, image: cv2.Mat, image_number: str, path: Path, id: int, width=600, height=120, save=False, savepath='./output') -> np.array:
        frame = paths2svg.big_bounding_box(path)
        frame = tuple(map(int, frame))
        document_crop = image[frame[2]:frame[3], frame[0]:frame[1]]
        tresh = otsu(document_crop)
        scan_crop_logic = document_crop < tresh
        original_width = int(frame[1]-frame[0])
        original_height = int(frame[3]-frame[2])
        box = Image.new('1', (original_width, original_height), "black")
        box_image = ImageDraw.Draw(box)
        box_image.polygon([(int(edge.point(0).real)-frame[0],
                            int(edge.point(0).imag)-frame[2]) for edge in path], fill="white", outline=None)
        img = np.logical_and(scan_crop_logic, box)
        img = np.invert(img)
        img = img.astype(float)
        img = cv2.resize(src=img, dsize=(width, height),
                         interpolation=cv2.INTER_NEAREST)
        if save:
            path = os.path.join(savepath, image_number)
            if not os.path.exists(path):
                os.makedirs(path)
            Image.fromarray(img > 0).save(os.path.join(path, f"{id}.png"))

        return np.asarray(img)

    def get_frames(self, save=False, savepath='./output') -> tuple:
        frames = np.array([self.__get_frame(image=document, image_number=os.path.splitext(os.path.basename(image))[
            0], path=path, id=attribute['id'], save=save, savepath=savepath) for image, document, frame in zip(self.images, self.documents, self.frames) for path, attribute in zip(*svg2paths(frame))])
        ids = np.array([attribute['id'] for _, frame in zip(
            self.images, self.frames) for _, attribute in zip(*svg2paths(frame))])
        return frames, ids


def main():
    frames, ids = Slicer(images=("./data/images", ".jpg"),
                         frames=("./data/ground-truth/locations", ".svg")).get_frames(save=True, savepath="./data/output/")


if __name__ == "__main__":
    main()
