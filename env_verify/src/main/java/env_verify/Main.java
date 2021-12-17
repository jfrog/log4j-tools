public class Main {
    static final String GLOBAL_FLAG = "LOG4J_FORMAT_MSG_NO_LOOKUPS";
    static final String COMMAND_FLAG = "log4j2.formatMsgNoLookups";
    static final String URL_TRUST_CODEBASE = "com.sun.jndi.ldap.object.trustURLCodebase";
    static final private String GREEN = "\u001b[32m";
    static final private String RED = "\u001b[31m";
    static final private String RESET_ALL = "\u001b[0m";

    private static void goodBadPrint(String s, boolean good) {
        if (good) {
            valuePrint(s, GREEN + "SET" + RESET_ALL);
        } else {
            valuePrint(s, RED + "NOT SET" + RESET_ALL);
        }
    }

    private static void valuePrint(String entry, String value){
        System.out.printf("%30s | %1s\n", entry, value);
    }

    private static boolean globalFlagCheck() {
        String answer = System.getenv(GLOBAL_FLAG);
        if (answer != null) {
            return answer.equalsIgnoreCase("true");
        }
        return false;
    }

    private static boolean commandFlagCheck() {
        String answer = System.getProperty(COMMAND_FLAG, "");
        if (answer.length() > 0) {
            return answer.equalsIgnoreCase("true");
        }
        return false;
    }

    private static String trustURLCodebase() {
        return System.getProperty(URL_TRUST_CODEBASE, "NOT SET");
    }

    private static String javaVersion() {
        return System.getProperty("java.vm.version", "");
    }

    public static void main(String[] args) {
        try {
            valuePrint("JVM version", javaVersion());
            valuePrint("trustURLCodebase", trustURLCodebase());
            goodBadPrint("log4j2.formatMsgNoLookups", commandFlagCheck());
            goodBadPrint("LOG4J_FORMAT_MSG_NO_LOOKUPS", globalFlagCheck());

        } catch (final SecurityException e) {
            //
        }
    }
}
