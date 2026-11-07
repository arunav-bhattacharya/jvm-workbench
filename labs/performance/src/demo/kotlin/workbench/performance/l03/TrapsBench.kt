package workbench.performance.l03

// JMH benchmarks must be Java classes in this lab (the annotation processor runs on Java only).
// This Kotlin twin runs the same Java benchmark through JMH's Runner API, but with JMH's
// normal output, so you can see every warm-up and measurement iteration as it happens.
import org.openjdk.jmh.runner.Runner
import org.openjdk.jmh.runner.options.OptionsBuilder
import org.openjdk.jmh.runner.options.VerboseMode

fun main() {
    val options = OptionsBuilder()
        .include(TrapsBench::class.java.name + ".sqrt(Discarded|Returned)")   // a regex: two of the five
        .verbosity(VerboseMode.NORMAL)
        .build()
    Runner(options).run()
}
