package log4shell_xray_wrapper;

import com.google.gson.Gson;
import com.google.gson.annotations.SerializedName;

public class ScanResults {
    static class CveInfo {
        @SerializedName("cve")
        String cve;
    }

    static class VulnerabilityInfo {
        @SerializedName("cves")
        CveInfo[] cves;
    }

    @SerializedName("vulnerabilities")
    VulnerabilityInfo[] vulns;

    public static ScanResults[] fromJson(String json) {
        return new Gson().fromJson(json, ScanResults[].class);
    }
}
