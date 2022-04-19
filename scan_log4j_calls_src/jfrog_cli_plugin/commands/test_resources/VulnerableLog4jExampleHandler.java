import org.apache.logging.log4j.LogManager;
import java.io.IOException;
import java.util.Scanner;
import org.apache.logging.log4j.Logger;

public class VulnerableLog4jExampleHandler
{
    Logger log = LogManager.getLogger();

    public void handle() throws IOException {
        final Scanner scanner = new Scanner(System.in);
        final String inputString = scanner.nextLine();
        log.info("Request User Agent:{}", (Object)inputString);
    }

    public void handle_nonvuln() throws IOException {
        log.info("Request User Agent: hardcoded");
    }

    public void handle_very_vuln() throws IOException {
        final Scanner scanner = new Scanner(System.in);
        final String inputString = scanner.nextLine();
        log.info(inputString);
    }

    public void handle_very_unvuln() throws IOException {
        final Scanner scanner = new Scanner(System.in);
        final String inputString = scanner.nextLine();
        log.info("Request User Agent:", (Object)"A", (Object)"b", (Object)"c", (Object)"d");
    }
}
