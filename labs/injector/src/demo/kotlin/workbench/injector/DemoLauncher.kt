package workbench.injector

import java.lang.reflect.InvocationTargetException
import kotlin.system.exitProcess

/**
 * Keep this file. `./gradlew :injector:demo -Pmain=<class>` starts every demo through it (see processorLab in
 * labs/build.gradle.kts): it calls the demo's main, then exits the JVM. The Kotlin compiler inside kctfork leaves
 * a non-daemon thread ("ApplicationImpl pooled thread 1") running, so a demo that compiles in memory would
 * otherwise print its output and then never finish.
 */
object DemoLauncher {
    @JvmStatic
    fun main(args: Array<String>) {
        val status = try {
            val demo = Class.forName(args.first())
            demo.getMethod("main", Array<String>::class.java).invoke(null, args.drop(1).toTypedArray())
            0
        } catch (e: InvocationTargetException) {
            e.cause?.printStackTrace()
            1
        }
        System.out.flush()
        exitProcess(status)
    }
}
