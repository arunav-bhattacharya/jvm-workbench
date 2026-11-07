package workbench.performance.l02

// JMH benchmarks must be Java classes in this lab (the annotation processor runs on Java only).
// This Kotlin twin runs the same Java benchmark through JMH's Runner API.
import org.openjdk.jmh.runner.Runner
import org.openjdk.jmh.runner.options.OptionsBuilder
import org.openjdk.jmh.runner.options.VerboseMode

fun main() {
    val options = OptionsBuilder()
        .include(MegamorphicBench::class.java.name)
        .param("types", "1", "3", "4")   // one type, three types, four types
        .verbosity(VerboseMode.SILENT)
        .build()
    println("types at the call site -> ns per batch of 1,024 fees")
    for (r in Runner(options).run()) {
        val s = r.primaryResult
        println("  %s type(s): %8.1f ns  (+/- %.1f)".format(r.params.getParam("types"), s.score, s.scoreError))
    }
}
