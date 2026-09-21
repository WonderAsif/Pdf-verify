import io
import re
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

def flawless_exact_tick_injection(input_pdf_bytes, password=""):
    reader = PdfReader(io.BytesIO(input_pdf_bytes))
    if reader.is_encrypted:
        if password:
            reader.decrypt(password)
        else:
            raise Exception("PDF is password protected. Please provide a password.")

    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    modified = False

    def scrub_xobject(xobj_ref, visited=None):
        if visited is None: visited = set()
        xobj = xobj_ref.get_object()
        
        obj_id = id(xobj)
        if obj_id in visited: return
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
