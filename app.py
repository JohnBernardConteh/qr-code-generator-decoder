# Core Pkgs
import streamlit as st
import numpy as np
import time
import cv2
from io import BytesIO

# For QR Code
import qrcode
from qrcode.exceptions import DataOverflowError

from PIL import Image


# Function to Load Image
def load_image(img):
    with Image.open(img) as im:
        return im.convert("RGB")


# Application
def main():
    # Heading with a navy and royal blue background.
    st.markdown(
        """
        <div style="
            background:linear-gradient(135deg, #0f172a, #2563eb);
            padding:25px;
            border-radius:12px;
            text-align:center;
            margin-bottom:25px;">
            <h1 style="
                color:white;
                font-size:36px;
                margin:0;">
                QR Code Generator &amp; Decoder
            </h1>
            <p style="
                color:#dbeafe;
                font-size:17px;
                margin:10px 0 0;">
                Generate, decode, and download QR codes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    menu = ["Home", "DecodeQR", "About"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Generate QR Code")

        # Text input
        with st.form(key="myqr_form"):
            raw_text = st.text_area(
                "Text Here",
                placeholder="Enter text or a website URL",
            )

            submit_button = st.form_submit_button("Generate")

        if submit_button:
            # Clear any previous result before generating.
            st.session_state.pop("generated_qr", None)

            if not raw_text.strip():
                st.warning("Enter some text or a URL.")
                return

            try:
                # Create a fresh QR object for each generation.
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )

                # Add Data
                qr.add_data(raw_text)

                # Generate
                qr.make(fit=True)

                img = qr.make_image(
                    fill_color="black",
                    back_color="white",
                )

                # Store PNG data in memory.
                image_buffer = BytesIO()
                img.save(image_buffer, format="PNG")

                timestr = time.strftime("%Y%m%d-%H%M%S")

                st.session_state["generated_qr"] = {
                    "image": image_buffer.getvalue(),
                    "text": raw_text,
                    "filename": f"generated_qr_{timestr}.png",
                }

            except DataOverflowError:
                st.error(
                    "The text is too long for one QR code. "
                    "Shorten it and try again."
                )
                return

        # Keep the generated result visible after downloading.
        if "generated_qr" in st.session_state:
            result = st.session_state["generated_qr"]

            # Layout
            col1, col2 = st.columns(2)

            with col1:
                final_img = load_image(
                    BytesIO(result["image"])
                )

                st.image(
                    final_img,
                    caption="Generated QR Code",
                )

                st.download_button(
                    label="Download QR Code",
                    data=result["image"],
                    file_name=result["filename"],
                    mime="image/png",
                    key="download_generated_qr",
                )

            with col2:
                st.info("Original Text")
                st.text(result["text"])

    elif choice == "DecodeQR":
        st.subheader("Decode QR Code")

        image_file = st.file_uploader(
            "Upload Image",
            type=["jpg", "png", "jpeg"],
        )

        if image_file is not None:
            file_bytes = np.frombuffer(
                image_file.getvalue(),
                dtype=np.uint8,
            )

            if file_bytes.size == 0:
                st.warning("The uploaded file is empty.")
                return

            try:
                opencv_image = cv2.imdecode(
                    file_bytes,
                    cv2.IMREAD_COLOR,
                )

                if opencv_image is None:
                    st.error(
                        "Could not read the image. "
                        "Upload a valid JPG or PNG file."
                    )
                    return

                c1, c2 = st.columns(2)

                with c1:
                    # OpenCV loads colour images in BGR order.
                    st.image(
                        opencv_image,
                        channels="BGR",
                        caption="Uploaded Image",
                    )

                with c2:
                    st.info("Decoded QR Code")

                    det = cv2.QRCodeDetector()

                    retval, points, straight_qrcode = (
                        det.detectAndDecode(opencv_image)
                    )

                    # Retval contains the decoded text.
                    if retval:
                        st.text(retval)

                        st.download_button(
                            label="Download Decoded Text",
                            data=retval.encode("utf-8"),
                            file_name="decoded_qr_text.txt",
                            mime="text/plain",
                            key="download_decoded_text",
                        )

                    elif points is not None:
                        st.warning(
                            "A QR code was detected, but its content "
                            "could not be decoded. Try a clearer image."
                        )

                    else:
                        st.warning(
                            "No QR code was detected in this image."
                        )

                    with st.expander("QR Detection Details"):
                        if points is not None:
                            st.write("Corner Points")

                            # Convert shape (1, 4, 2) into (4, 2).
                            corner_points = points.reshape(-1, 2)

                            st.dataframe({
                                "X": corner_points[:, 0],
                                "Y": corner_points[:, 1],
                            })

                        if (
                            straight_qrcode is not None
                            and straight_qrcode.size > 0
                        ):
                            st.image(
                                straight_qrcode,
                                caption="Straightened QR Code",
                                clamp=True,
                            )

            except cv2.error as exc:
                st.error(f"Could not process the image: {exc}")

            except UnicodeDecodeError:
                st.error(
                    "The QR content could not be read as UTF-8 text."
                )

    else:
        st.subheader("About")

        st.write(
            "QR Code Generator & Decoder lets you create QR codes "
            "from text or URLs and download them as PNG images. "
            "Upload a QR code image to read its content and "
            "download the decoded text."
        )

        st.write("Developed by John Bernard Conteh.")


if __name__ == "__main__":
    main()
    