package workbench.memory;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Starts a fresh JVM with extra flags and the same classpath. Gradle starts the demo JVM for you,
 * so a demo that wants to show what a flag changes runs its experiment in a child JVM instead.
 */
public final class Jvm {
    private Jvm() {}

    /** Runs {@code mainClass} in a child JVM with {@code flags}. Its output goes straight to this console. */
    public static int run(List<String> flags, String mainClass, String... args) {
        try {
            return new ProcessBuilder(command(flags, mainClass, args)).inheritIO().start().waitFor();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return -1;
        }
    }

    /** Same as {@link #run}, but returns the child's stdout and stderr lines instead of printing them. */
    public static List<String> lines(List<String> flags, String mainClass, String... args) {
        List<String> out = new ArrayList<>();
        try {
            Process p = new ProcessBuilder(command(flags, mainClass, args)).redirectErrorStream(true).start();
            try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
                for (String line; (line = r.readLine()) != null; ) {
                    if (!line.startsWith("Picked up JAVA_TOOL_OPTIONS")) out.add(line);
                }
            }
            p.waitFor();
            return out;
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return out;
        }
    }

    private static List<String> command(List<String> flags, String mainClass, String... args) {
        List<String> cmd = new ArrayList<>();
        cmd.add(ProcessHandle.current().info().command().orElse("java"));   // the same java binary
        cmd.addAll(flags);
        cmd.add("-cp");
        cmd.add(System.getProperty("java.class.path"));                     // the same classpath
        cmd.add(mainClass);
        cmd.addAll(List.of(args));
        return cmd;
    }
}
