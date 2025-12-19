# app\willbedeleted\utils\file_utils\xml_utils.py
class UtilsXML:
    @staticmethod
    def parse_react_data(react, namespace, run_id="FAM"):
        """
        Verilen react öğesinden gerekli bilgileri çıkarır.
        """
        row = {}
        row["React ID"] = react.get("id", "")
        sample = react.find("rdml:sample", namespaces=namespace)
        row["Barkot No"] = sample.get("id") if sample is not None else ""
        tar = react.find(".//rdml:tar", namespaces=namespace)
        row["Hasta Adı"] = tar.get("id") if tar is not None else ""
        cq = react.find(".//rdml:cq", namespaces=namespace)
        row[f"{run_id} Ct"] = round(float(cq.text), 6) if cq is not None else ""
        adps = react.findall(".//rdml:adp", namespaces=namespace)
        coords = [
            (
                int(adp.find("rdml:cyc", namespaces=namespace).text),
                round(float(adp.find("rdml:fluor", namespaces=namespace).text), 6),
            )
            for adp in adps
        ]
        row[f"{run_id} koordinat list"] = str(coords)
        return row

    @staticmethod
    def extract_run(root, run_id, namespace):
        """
        Verilen run ID'ye sahip bir koşuyu döndürür.
        """
        run = root.find(f".//rdml:run[@id='{run_id}']", namespaces=namespace)
        if not run:
            raise ValueError(f"'{run_id}' koşusu bulunamadı.")
        return run
