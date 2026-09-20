import flet as ft
from pypdf import PdfReader, PdfWriter
import io
import re

def flawless_exact_tick_injection(input_pdf_bytes, password=""):
    """
    Pure Python implementation using pypdf for Android compatibility.
    Manipulates raw PDF streams to inject the vector tick and remove invalid text.
    """
    reader = PdfReader(io.BytesIO(input_pdf_bytes))
    
    if reader.is_encrypted:
        if password:
            reader.decrypt(password)
        else:
            raise ValueError("PDF is protected. Password required.")

    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    modified = False

    def process_stream_data(stream_bytes, w, h):
        try:
            stream_str = stream_bytes.decode('latin1')
            original_str = stream_str

            # Erase background layers and text strings
            stream_str = stream_str.replace("/n0 Do", " ")
            stream_str = stream_str.replace("/n1 Do", " ")
            stream_str = stream_str.replace("Signature Not Verified", "Signature valid")
            stream_str = stream_str.replace("Not Verified", "valid")

            # Erase residual yellow shapes
            stream_str = re.sub(r'0\.?\d* 0\.?\d* 1(?:\.0+)? 0\.?\d* [kK]', '0 0 0 0 k', stream_str)
            stream_str = re.sub(r'1(?:\.0+)? 1(?:\.0+)? 0\.?\d* [rR][gG]', '1 1 1 rg', stream_str)
            stream_str = re.sub(r'1(?:\.0+)? 0\.[89]\d* 0\.?\d* [rR][gG]', '1 1 1 rg', stream_str)

            # Shifted exactly to match the second reference image
            p1x, p1y = w * 0.38, h * 0.45  
            p2x, p2y = w * 0.48, h * 0.22  
            p3x, p3y = w * 0.64, h * 0.76  

            green_w = w * 0.05
            outline_w = green_w + (w * 0.015)
            shadow_x = w * 0.015
            shadow_y = h * 0.025

            tick_stream = f"""
            q
            0 j 2 J
            {outline_w} w
            0 0 0 RG
            {p1x + shadow_x} {p1y - shadow_y} m
            {p2x + shadow_x} {p2y - shadow_y} l
            {p3x + shadow_x} {p3y - shadow_y} l
            S
            {p1x} {p1y} m
            {p2x} {p2y} l
            {p3x} {p3y} l
            S
            {green_w} w
            0 0.6 0.15 RG
            {p1x} {p1y} m
            {p2x} {p2y} l
            {p3x} {p3y} l
            S
            Q
            """

            # Inject before "BT" to ensure the tick stays behind the black text
            bt_index = stream_str.find("BT")
            if bt_index != -1:
                final_stream = stream_str[:bt_index] + "\n" + tick_stream + "\n" + stream_str[bt_index:]
            else:
                final_stream = tick_stream + "\n" + stream_str

            return final_stream.encode('latin1'), final_stream != original_str
        except Exception:
            return stream_bytes, False

    for page in writer.pages:
        if "/Annots" in page:
            for annot_ref in page["/Annots"]:
                annot = annot_ref.get_object()
                
                # Check if annotation is a Signature field
                if annot.get("/FT") == "/Sig":
                    rect = annot.get("/Rect")
                    w = float(rect[2] - rect[0])
                    h = float(rect[3] - rect[1])
                    
                    ap = annot.get("/AP")
                    if ap and "/N" in ap:
                        n_stream = ap["/N"].get_object()
                        
                        # Extract uncompressed stream data
                        stream_bytes = n_stream.get_data()
                        new_bytes, is_mod = process_stream_data(stream_bytes, w, h)
                        
                        if is_mod:
                            n_stream._data = new_bytes
                            # Remove filter to prevent pypdf from trying to re-compress with old parameters
                            if "/Filter" in n_stream:
                                del n_stream["/Filter"]
                            modified = True

    if modified:
        output_pdf = io.BytesIO()
        writer.write(output_pdf)
        return output_pdf.getvalue()

    return None

# --- Flet UI Setup ---
def main(page: ft.Page):
    page.title = "Exact Image Replica Stamper"
    page.scroll = "adaptive"
    page.padding = 20
    
    uploaded_file_bytes = None
    file_name_display = ft.Text("No file selected", color=ft.Colors.GREY)

    def on_file_picked(e: ft.FilePickerResultEvent):
        nonlocal uploaded_file_bytes
        if e.files and len(e.files) > 0:
            with open(e.files[0].path, "rb") as f:
                uploaded_file_bytes = f.read()
            file_name_display.value = f"Selected: {e.files[0].name}"
            file_name_display.color = ft.Colors.BLUE
            status_text.value = ""
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    password_input = ft.TextField(label="PDF Password (optional)", password=True, width=300)
    status_text = ft.Text("", weight="bold")

    def apply_stamp(e):
        if uploaded_file_bytes is None:
            status_text.value = "Please select a PDF first."
            status_text.color = ft.Colors.RED
            page.update()
            return
            
        try:
            stamped_bytes = flawless_exact_tick_injection(uploaded_file_bytes, password=password_input.value)
            if stamped_bytes:
                out_filename = "/storage/emulated/0/Download/image_replica_stamp.pdf"
                with open(out_filename, "wb") as f:
                    f.write(stamped_bytes)
                status_text.value = f"Success! Saved to Downloads folder."
                status_text.color = ft.Colors.GREEN
            else:
                status_text.value = "Error: No signature field found to replace."
                status_text.color = ft.Colors.RED
        except Exception as ex:
            status_text.value = f"Error: {str(ex)}"
            status_text.color = ft.Colors.RED
        page.update()

    page.add(
        ft.Text("PDF Stamper", size=28, weight="bold"),
        ft.Text("Injects the green tick exactly into the signature block."),
        ft.Divider(),
        ft.ElevatedButton("1. Choose a PDF file", icon=ft.Icons.UPLOAD_FILE, on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["pdf"])),
        file_name_display,
        password_input,
        ft.ElevatedButton("2. Apply Stamp", icon=ft.Icons.CHECK_CIRCLE, on_click=apply_stamp, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
        status_text
    )

ft.run(main)
