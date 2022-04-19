package log4shell_xray_wrapper;

import static org.junit.Assert.assertTrue;

import org.junit.Test;

/**
 * Unit test for simple App.
 */
public class AppTest 
{
    /**
     * Rigorous Test :-)
     */
    @Test
    public void shouldAnswerWithTrue()
    {
        assertTrue( true );
    }

    @Test public void LoadJson() {
        ScanResults[] res = ScanResults.fromJson("[\n" +
                "  {\n" +
                "    \"scan_id\": \"9414d26c-a46f-458b-7c1e-d99b311d40e3\",\n" +
                "    \"vulnerabilities\": [\n" +
                "      {\n" +
                "        \"cves\": [\n" +
                "          {\n" +
                "            \"cvss_v2_score\": \"7.1\",\n" +
                "            \"cvss_v2_vector\": \"CVSS:2.0/AV:N/AC:M/Au:N/C:N/I:N/A:C\",\n" +
                "            \"cvss_v3_score\": \"7.5\",\n" +
                "            \"cvss_v3_vector\": \"CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H\"\n" +
                "          }\n" +
                "        ],\n" +
                "        \"summary\": \"FasterXML jackson-databind node/NodeSerialization.java NodeSerialization::readExternal() Function JDK Serialization Memory Exhaustion DoS\",\n" +
                "        \"severity\": \"High\",\n" +
                "        \"components\": {\n" +
                "          \"gav://com.fasterxml.jackson.core:jackson-databind:2.13.0\": {\n" +
                "            \"fixed_versions\": [\n" +
                "              \"[2.14.0]\",\n" +
                "              \"[2.13.1]\",\n" +
                "              \"[2.12.6]\"\n" +
                "            ],\n" +
                "            \"impact_paths\": [\n" +
                "              [\n" +
                "                {\n" +
                "                  \"component_id\": \"gav://fr.christophetd.log4shell:log4shell-vulnerable-app:0.0.1-SNAPSHOT\"\n" +
                "                },\n" +
                "                {\n" +
                "                  \"component_id\": \"gav://org.springframework.boot:spring-boot-starter-web:2.6.1\"\n" +
                "                },\n" +
                "                {\n" +
                "                  \"component_id\": \"gav://org.springframework.boot:spring-boot-starter-json:2.6.1\"\n" +
                "                },\n" +
                "                {\n" +
                "                  \"component_id\": \"gav://com.fasterxml.jackson.core:jackson-databind:2.13.0\"\n" +
                "                }\n" +
                "              ]\n" +
                "            ]\n" +
                "          }\n" +
                "        },\n" +
                "        \"issue_id\": \"XRAY-191477\"\n" +
                "      },\n" +
                "      {\n" +
                "        \"cves\": [\n" +
                "          {\n" +
                "            \"cve\": \"CVE-2021-45105\",\n" +
                "            \"cvss_v2_score\": \"5.0\",\n" +
                "            \"cvss_v2_vector\": \"CVSS:2.0/AV:N/AC:L/Au:N/C:N/I:N/A:P\",\n" +
                "            \"cvss_v3_score\": \"7.5\",\n" +
                "            \"cvss_v3_vector\": \"CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H\"\n" +
                "          }\n" +
                "        ],\n" +
                "        \"summary\": \"[CVE-2021-45105] Apache Log4j2 versions 2.0-alpha1 through 2.16.0 did not protect from uncontrolled recursion from self-referential lookups.\",\n" +
                "        \"severity\": \"High\",\n" +
                "        \"components\": {\n" +
                "          \"gav://org.apache.logging.log4j:log4j-core:2.15.0\": {\n" +
                "            \"fixed_versions\": [\n" +
                "              \"[2.17.0]\",\n" +
                "              \"[2.12.3]\",\n" +
                "              \"[2.3.1]\"\n" +
                "            ],\n" +
                "            \"impact_paths\": [\n" +
                "              [\n" +
                "                {\n" +
                "                  \"component_id\": \"gav://fr.christophetd.log4shell:log4shell-vulnerable-app:0.0.1-SNAPSHOT\"\n" +
                "                },\n" +
                "                {\n" +
                "                  \"component_id\": \"gav://org.springframework.boot:spring-boot-starter-log4j2:2.6.1\"\n" +
                "                },\n" +
                "                {\n" +
                "                  \"component_id\": \"gav://org.apache.logging.log4j:log4j-core:2.15.0\"\n" +
                "                }\n" +
                "              ]\n" +
                "            ]\n" +
                "          }\n" +
                "        },\n" +
                "        \"issue_id\": \"XRAY-192348\"\n" +
                "      },\n" +
                "      {\n" +
                "        \"cves\": [\n" +
                "          {\n" +
                "            \"cve\": \"CVE-2021-45046\",\n" +
                "            \"cvss_v2_score\": \"5.1\",\n" +
                "            \"cvss_v2_vector\": \"CVSS:2.0/AV:N/AC:H/Au:N/C:P/I:P/A:P\",\n" +
                "            \"cvss_v3_score\": \"9.0\",\n" +
                "            \"cvss_v3_vector\": \"CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:C/C:H/I:H/A:H\"\n" +
                "          }\n" +
                "        ],\n" +
                "        \"summary\": \"It was found that the fix to address CVE-2021-44228 in Apache Log4j 2.15.0 was incomplete in certain non-default configurations. This could allows attackers with control over Thread Context Map (MDC) input data when the logging configuration uses a non-default Pattern Layout with either a Context Lookup (for example, $${ctx:loginId}) or a Thread Context Map pattern (%X, %mdc, or %MDC) to craft malicious input data using a JNDI Lookup pattern resulting in an information leak and remote code execution in some environments and local code execution in all environments. Log4j 2.16.0 (Java 8) and 2.12.2 (Java 7) fix this issue by removing support for message lookup patterns and disabling JNDI functionality by default.\",\n" +
                "        \"severity\": \"Critical\",\n" +
                "        \"components\": {\n" +
                "          \"gav://org.apache.logging.log4j:log4j-core:2.15.0\": {\n" +
                "            \"fixed_versions\": [\n" +
                "              \"[2.16.0]\",\n" +
                "              \"[2.12.2]\",\n" +
                "              \"[2.3.1]\"\n" +
                "            ],\n" +
                "            \"impact_paths\": [\n" +
                "              [\n" +
                "                {\n" +
                "                  \"component_id\": \"gav://fr.christophetd.log4shell:log4shell-vulnerable-app:0.0.1-SNAPSHOT\"\n" +
                "                },\n" +
                "                {\n" +
                "                  \"component_id\": \"gav://org.springframework.boot:spring-boot-starter-log4j2:2.6.1\"\n" +
                "                },\n" +
                "                {\n" +
                "                  \"component_id\": \"gav://org.apache.logging.log4j:log4j-core:2.15.0\"\n" +
                "                }\n" +
                "              ]\n" +
                "            ]\n" +
                "          }\n" +
                "        },\n" +
                "        \"issue_id\": \"XRAY-192126\"\n" +
                "      }\n" +
                "    ],\n" +
                "    \"component_id\": \"gav://fr.christophetd.log4shell:log4shell-vulnerable-app:0.0.1-SNAPSHOT\",\n" +
                "    \"package_type\": \"Maven\",\n" +
                "    \"status\": \"completed\"\n" +
                "  }\n" +
                "]");
    }
}
