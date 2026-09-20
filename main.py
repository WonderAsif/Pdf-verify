from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
import io
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject
import re

class PdfStamperApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        title = Label(
            text="[b]PDF Signature Stamper[/b]",
            markup=True,
            size_hint_y=0.15,
            font_size='20sp'
        )
        layout.add_widget(title)
        
        select_btn = Button(
            text="Select PDF File",
            size_hint_y=0.15,
            background_color=(0.2, 0.6, 0.8, 1)
        )
        select_btn.bind(on_press=self.select_file)
        layout.add_widget(select_btn)
        
        scroll = ScrollView(size_hint_y=0.7)
        self.status_label = Label(
            text="Ready. Select a PDF to stamp signature.",
            size_hint_y=None,
            valign='top',
            padding=(10, 10)
        )
        self.status_label.bind(texture_size=self.status_label.setter('size'))
        scroll.add_widget(self.status_label)
        layout.add_widget(scroll)
        
        return layout
    
    def select_file(self, instance):
        try:
            from plyer import filechooser
            filechooser.open_file(
                filters=["*.pdf"],
                on_selection=self.process_pdf
            )
        except Exception as e:
            self.status_label.text = f"Error opening file picker: {str(e)}"
    
    def process_pdf(self, selection):
        if not selection:
            self.status_label.text = "No file selected."
            return
        
        try:
            filepath = selection[0]
            self.status_label.text = f"Processing:\n{filepath}\n\nPlease wait..."
            
            with open(filepath, 'rb') as f:
                pdf_bytes = f.read()
            
            stamped = self.stamp_signature(pdf_bytes)
            
            if stamped:
                output_path = filepath.replace('.pdf', '_stamped.pdf')
                if output_path == filepath:
                    output_path = filepath.replace('.pdf', '') + '_stamped.pdf'
                
                with open(output_path, 'wb') as f:
                    f.write(stamped)
                
                self.status_label.text = (
                    f"✓ SUCCESS!\n\n"
                    f"Stamped PDF saved to:\n{output_path}\n\n"
                    f"File size: {len(stamped) / 1024:.1f} KB"
                )
            else:
                self.status_label.text = "✗ No signature field found in PDF."
                
        except Exception as e:
            self.status_label.text = f"✗ Error:\n{str(e)}"
    
    def stamp_signature(self, input_pdf_bytes, password=""):
        reader = PdfReader(io.BytesIO(input_pdf_bytes))
        if reader.is_encrypted:
            if password:
                reader.decrypt(password)
            else:
                raise Exception("PDF is password protected.")

        writer = PdfWriter()
        writer.append_pages_from_reader(reader)
        modified = False

        def scrub_xobject(xobj_ref, visited=None):
            if visited is None:
                visited = set()
            xobj = xobj_ref.get_object()
            obj_id = id(xobj)
            if obj_id in visited:
                return
            visited.add(obj_id)

            try:
                data = xobj.get_data()
                stream_str = data.decode('latin1')
                original_str = stream_str

                stream_str = stream_str.replace("/n0 Do", " ")
                stream_str = stream_str.replace("/n1 Do", " ")
                stream_str = stream_str.replace("Signature Not Verified", "Signature valid")
                stream_str = stream_str.replace("Not Verified", "valid")
                stream_str = re.sub(r'0\.?\d* 0\.?\d* 1(?:\.0+)? 0\.?\d* [kK]', '0 0 0 0 k', stream_str)
                stream_str = re.sub(r'1(?:\.0+)? 1(?:\.0+)? 0\.?\d* [rR][gG]', '1 1 1 rg', stream_str)
                stream_str = re.sub(r'1(?:\.0+)? 0\.[89]\d* 0\.?\d* [rR][gG]', '1 1 1 rg', stream_str)

                if stream_str != original_str:
                    xobj._data = stream_str.encode('latin1')
                    if NameObject("/Filter") in xobj:
                        del xobj[NameObject("/Filter")]

                if NameObject("/Resources") in xobj:
                    res = xobj[NameObject("/Resources")]
                    if NameObject("/XObject") in res:
                        xobjs = res[NameObject("/XObject")]
                        for key in xobjs:
                            scrub_xobject(xobjs[key], visited)
            except Exception:
                pass

        for page in writer.pages:
            if NameObject("/Annots") not in page:
                continue

            for annot_ref in page[NameObject("/Annots")]:
                annot = annot_ref.get_object()

                if annot.get(NameObject("/Subtype")) == NameObject("/Widget") and annot.get(NameObject("/FT")) == NameObject("/Sig"):
                    if NameObject("/AP") in annot and NameObject("/N") in annot[NameObject("/AP")]:
                        ap_n_ref = annot[NameObject("/AP")][NameObject("/N")]
                        ap_n = ap_n_ref.get_object()

                        scrub_xobject(ap_n_ref)

                        try:
                            stream_str = ap_n.get_data().decode('latin1')
                            bbox = ap_n.get(NameObject("/BBox"))
                            if bbox:
                                w = float(bbox[2]) - float(bbox[0])
                                h = float(bbox[3]) - float(bbox[1])
                            else:
                                rect = annot.get(NameObject("/Rect"))
                                w = float(rect[2]) - float(rect[0])
                                h = float(rect[3]) - float(rect[1])

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

                            bt_index = stream_str.find("BT")
                            if bt_index != -1:
                                final_stream = stream_str[:bt_index] + "\n" + tick_stream + "\n" + stream_str[bt_index:]
                            else:
                                final_stream = tick_stream + "\n" + stream_str

                            ap_n._data = final_stream.encode('latin1')
                            if NameObject("/Filter") in ap_n:
                                del ap_n[NameObject("/Filter")]

                            modified = True
                        except Exception:
                            pass

        if modified:
            output_pdf = io.BytesIO()
            writer.write(output_pdf)
            return output_pdf.getvalue()
        return None


if __name__ == '__main__':
    PdfStamperApp().run()
    
