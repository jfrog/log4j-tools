package org.owasp.webgoat.application.documentation_samples;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.ServletException;
import java.io.IOException;

public class command_inj_vuln {
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String cmd = "ping -c 1 " + request.getParameter("ip");
        Process proc = Runtime.getRuntime().exec(cmd);
        if (proc.exitValue() == 0) {
            response.setStatus(HttpServletResponse.SC_OK);
        } else {
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
        }
    }
}
