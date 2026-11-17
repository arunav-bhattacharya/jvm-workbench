package workbench.performance.l06

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class FlameGraphTest {

    // seven real lines from an async-profiler 4.6 CPU profile of SlowReport.readingSeconds on JDK 25
    // (the thread frames below SlowReport.lambda$hammer$0 are cut off); the two format lines ending in
    // "Formatter.format 10" and "Formatter.format 4" really were separate lines in the profile
    private val real = """
        workbench/performance/l06/SlowReport.lambda${'$'}hammer${'$'}0;workbench/performance/l06/SlowReport.readingSeconds;java/util/regex/Pattern.compile;java/util/regex/Pattern.<init>;java/util/regex/Pattern.compile 26
        workbench/performance/l06/SlowReport.lambda${'$'}hammer${'$'}0;os::javaTimeNanos;clock_gettime@@GLIBC_2.17;__vdso_clock_gettime 24
        workbench/performance/l06/SlowReport.lambda${'$'}hammer${'$'}0;workbench/performance/l06/SlowReport.readingSeconds;java/util/regex/Pattern.matcher;java/util/regex/Matcher.<init>;java/util/regex/Matcher.reset 12
        workbench/performance/l06/SlowReport.lambda${'$'}hammer${'$'}0;workbench/performance/l06/SlowReport.readingSeconds;java/lang/String.format;java/util/Formatter.format;java/util/Formatter.format 10
        workbench/performance/l06/SlowReport.lambda${'$'}hammer${'$'}0;workbench/performance/l06/SlowReport.readingSeconds;java/lang/String.format;java/util/Formatter.format;java/util/Formatter.format 4
        workbench/performance/l06/SlowReport.lambda${'$'}hammer${'$'}0;workbench/performance/l06/SlowReport.readingSeconds;java/lang/String.format;java/util/Formatter.format;java/util/Formatter.format;itable stub 7
        workbench/performance/l06/SlowReport.lambda${'$'}hammer${'$'}0;workbench/performance/l06/SlowReport.readingSeconds;java/lang/String.split;java/lang/String.split;java/lang/String.split;java/lang/String.indexOf;java/lang/StringLatin1.indexOf 79
    """.trimIndent().lines()

    private val samples by lazy { real.mapNotNull(FlameGraph::parse) }

    private val reading = "workbench/performance/l06/SlowReport.readingSeconds"

    @Test
    fun `parses a line, including frame names with spaces`() {
        val s = FlameGraph.parse("a;b;itable stub 3")
        assertThat(s).isEqualTo(Sample(listOf("a", "b", "itable stub"), 3))
        assertThat(FlameGraph.parse("   ")).isNull()
        assertThat(samples).hasSize(7)
        assertThat(samples.sumOf { it.count }).isEqualTo(162)
    }

    @Test
    fun `self time goes to the top frame only`() {
        val self = FlameGraph.selfTime(samples)
        assertThat(self["java/util/regex/Pattern.compile"]).isEqualTo(26)
        assertThat(self["java/util/Formatter.format"]).isEqualTo(14)
        assertThat(self["itable stub"]).isEqualTo(7)
        assertThat(self["java/lang/StringLatin1.indexOf"]).isEqualTo(79)
        assertThat(self[reading]).isNull()                              // never on top in these samples
        assertThat(self.values.sum()).isEqualTo(162)
    }

    @Test
    fun `inclusive time counts a frame once per sample, even when it repeats in the stack`() {
        val incl = FlameGraph.inclusiveTime(samples)
        assertThat(incl[reading]).isEqualTo(138)
        assertThat(incl["java/util/regex/Pattern.compile"]).`as`("Pattern.compile appears twice in one stack").isEqualTo(26)
        assertThat(incl["java/lang/String.split"]).`as`("String.split appears three times in one stack").isEqualTo(79)
        assertThat(incl["java/util/Formatter.format"]).isEqualTo(21)
        assertThat(incl["java/util/regex/Matcher.<init>"]).isEqualTo(12)
    }

    @Test
    fun `build merges equal prefixes into one box and sorts children alphabetically`() {
        val root = FlameGraph.build(samples)
        assertThat(root.name).isEqualTo("all")
        assertThat(root.total).isEqualTo(162)
        val lambda = root.children.single()
        // alphabetical, not by width: "os::" sorts before "workbench/", although it is the narrower box
        assertThat(lambda.children.map { it.name }).containsExactly("os::javaTimeNanos", reading)
        val readingSeconds = lambda.children.last()
        assertThat(readingSeconds.total).isEqualTo(138)
        assertThat(readingSeconds.self).isZero()
        assertThat(readingSeconds.children.map { it.name }).containsExactly(
            "java/lang/String.format", "java/lang/String.split",
            "java/util/regex/Pattern.compile", "java/util/regex/Pattern.matcher")
        assertThat(readingSeconds.children.map { it.total }).containsExactly(21L, 79L, 26L, 12L)
        val outerFormat = readingSeconds.children[0].children.single()
        val innerFormat = outerFormat.children.single()
        assertThat(outerFormat.total).isEqualTo(21)
        assertThat(innerFormat.self).`as`("10 + 4 merged, minus the 7 in itable stub").isEqualTo(14)
    }

    @Test
    fun `the hottest path follows the widest box at every level`() {
        assertThat(FlameGraph.hottestPath(FlameGraph.build(samples))).containsExactly(
            "workbench/performance/l06/SlowReport.lambda\$hammer\$0", reading,
            "java/lang/String.split", "java/lang/String.split", "java/lang/String.split",
            "java/lang/String.indexOf", "java/lang/StringLatin1.indexOf")
    }
}
