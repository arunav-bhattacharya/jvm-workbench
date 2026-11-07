package workbench.bytecode.l07

import java.lang.instrument.ClassFileTransformer
import java.lang.instrument.Instrumentation
import java.nio.file.Files
import java.security.ProtectionDomain
import java.util.concurrent.atomic.AtomicInteger
import java.util.jar.Attributes
import java.util.jar.JarOutputStream
import java.util.jar.Manifest

/** A startup agent: the JVM calls premain before main. It watches classes load and changes nothing. */
object KCountingAgent {
    @JvmStatic
    fun premain(args: String?, inst: Instrumentation) {
        println("[agent] premain args=$args, classes already loaded: ${inst.allLoadedClasses.size}")
        val seen = AtomicInteger()
        inst.addTransformer(object : ClassFileTransformer {
            override fun transform(
                loader: ClassLoader?, className: String?, classBeingRedefined: Class<*>?,
                domain: ProtectionDomain?, classfileBuffer: ByteArray,
            ): ByteArray? {
                seen.incrementAndGet()
                if (className?.startsWith("workbench/") == true) {
                    println("[agent] loading $className (${classfileBuffer.size} bytes)")
                }
                return null                        // null means "no change"
            }
        })
        Runtime.getRuntime().addShutdownHook(Thread { println("[agent] transformer saw ${seen.get()} class definitions") })
    }
}

data class KPayment(val id: String, val amountMinor: Long)

/** The program the startup agent watches. */
object KAgentTarget {
    @JvmStatic
    fun main(args: Array<String>) {
        println("main: started")
        val p = KPayment("p-1", 1_250)            // KPayment is loaded here, on first use
        println("main: $p")
    }
}

/** Builds a one-line agent jar and starts a second JVM with -javaagent, so you can watch premain run. */
fun main() {
    // 1. an agent jar needs a manifest naming the agent class; the class itself is on the class path
    val jar = Files.createTempFile("counting-agent", ".jar")
    val manifest = Manifest().apply {
        mainAttributes[Attributes.Name.MANIFEST_VERSION] = "1.0"
        mainAttributes.putValue("Premain-Class", KCountingAgent::class.java.name)
    }
    JarOutputStream(Files.newOutputStream(jar), manifest).use { }   // no entries needed

    // 2. java -javaagent:<jar>=payments -cp <this class path> KAgentTarget
    val java = ProcessHandle.current().info().command().orElse("java")
    val child = ProcessBuilder(java, "-javaagent:$jar=payments", "-cp", System.getProperty("java.class.path"),
        KAgentTarget::class.java.name)
        .redirectErrorStream(true)
        .start()
    child.inputStream.transferTo(System.out)
    println("child JVM exited with ${child.waitFor()}")
    Files.delete(jar)
}
