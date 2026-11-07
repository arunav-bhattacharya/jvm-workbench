package workbench.bytecode.l07;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.jar.Attributes;
import java.util.jar.JarOutputStream;
import java.util.jar.Manifest;

/** Builds a one-line agent jar and starts a second JVM with -javaagent, so you can watch premain run. */
public class StartupAgentDemo {
    public static void main(String[] args) throws Exception {
        // 1. an agent jar needs a manifest naming the agent class; the class itself is on the class path
        Path jar = Files.createTempFile("counting-agent", ".jar");
        Manifest manifest = new Manifest();
        manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
        manifest.getMainAttributes().putValue("Premain-Class", CountingAgent.class.getName());
        try (JarOutputStream out = new JarOutputStream(Files.newOutputStream(jar), manifest)) {
            // no entries needed
        }

        // 2. java -javaagent:<jar>=payments -cp <this class path> AgentTarget
        String java = ProcessHandle.current().info().command().orElse("java");
        Process child = new ProcessBuilder(java, "-javaagent:" + jar + "=payments",
                "-cp", System.getProperty("java.class.path"), AgentTarget.class.getName())
                .redirectErrorStream(true)
                .start();
        child.getInputStream().transferTo(System.out);
        System.out.println("child JVM exited with " + child.waitFor());
        Files.delete(jar);
    }
}
