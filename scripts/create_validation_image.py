import argparse
import json


# Creates "validation" images with rectangles for the bounding box information that
# Claude creates when determining where to add text annotations in PDFs. See forms.md.


def create_validation_image(page_number, fields_json_path, input_path, output_path):
    from PIL import Image, ImageDraw

    # Input file should be in the `fields.json` format described in forms.md.
    with open(fields_json_path, 'r') as f:
        data = json.load(f)

        img = Image.open(input_path)
        draw = ImageDraw.Draw(img)
        num_boxes = 0
        
        for field in data["form_fields"]:
            if field["page_number"] == page_number:
                entry_box = field['entry_bounding_box']
                label_box = field['label_bounding_box']
                # Draw red rectangle over entry bounding box and blue rectangle over the label.
                draw.rectangle(entry_box, outline='red', width=2)
                draw.rectangle(label_box, outline='blue', width=2)
                num_boxes += 2
        
        img.save(output_path)
        print(f"Created validation image at {output_path} with {num_boxes} bounding boxes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create validation image with bounding boxes from fields.json.")
    parser.add_argument("page_number", type=int, help="Page number to validate")
    parser.add_argument("fields_json", help="fields.json file (see forms.md)")
    parser.add_argument("input_image", help="Input image path")
    parser.add_argument("output_image", help="Output image path")
    args = parser.parse_args()
    create_validation_image(args.page_number, args.fields_json, args.input_image, args.output_image)
