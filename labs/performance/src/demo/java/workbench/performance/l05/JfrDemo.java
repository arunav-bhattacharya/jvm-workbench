package workbench.performance.l05;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Runs PaymentWorkload for 4 seconds in a second JVM started with
 * -XX:StartFlightRecording:filename=build/perf05.jfr,settings=profile
 * and tells you where the recording is.
 */
public class JfrDemo {
    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("child")) { PaymentWorkload.run(4); return; }
        Path file = Path.of("build", "perf05.jfr").toAbsolutePath();
        String java = ProcessHandle.current().info().command().orElse("java");
        List<String> cmd = new ArrayList<>(List.of(java,
                "-XX:StartFlightRecording:filename=" + file + ",settings=profile",
                "-cp", System.getProperty("java.class.path"), JfrDemo.class.getName(), "child"));
        Process p = new ProcessBuilder(cmd).inheritIO().start();
        p.waitFor();
        System.out.println("recording written to " + file);
        System.out.println("try: jfr summary " + file);
    }
}
