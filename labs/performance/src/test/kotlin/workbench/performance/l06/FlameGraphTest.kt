package workbench.performance.l06

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class FlameGraphTest {

    // trimmed from a real async-profiler CPU profile of the slow fee code (the thread-pool frames
    // below PaymentSim.lambda$main$0 are cut off); the two 91/78 lines really were separate lines
    private val real = """
        PaymentSim.lambda${'$'}main${'$'}0;PaymentSim.feeSlow;java/util/regex/Pattern.compile;java/util/regex/Pattern.<init>;java/util/regex/Pattern.compile 645
        PaymentSim.lambda${'$'}main${'$'}0;os::javaTimeNanos;clock_gettime@@GLIBC_2.17;__vdso_clock_gettime 206
        PaymentSim.lambda${'$'}main${'$'}0;PaymentSim.feeSlow;java/util/regex/Pattern.matcher;java/util/regex/Matcher.<init>;java/util/regex/Matcher.reset 140
        PaymentSim.lambda${'$'}main${'$'}0;PaymentSim.feeSlow;java/lang/String.format;java/util/Formatter.format;java/util/Formatter.format 91
        PaymentSim.lambda${'$'}main${'$'}0;PaymentSim.feeSlow;java/lang/String.format;java/util/Formatter.format;java/util/Formatter.format 78
        PaymentSim.lambda${'$'}main${'$'}0;PaymentSim.feeSlow;java/util/regex/Pattern.matcher;java/util/regex/Matcher.<init> 80
        PaymentSim.lambda${'$'}main${'$'}0;PaymentSim.feeSlow;java/lang/String.format;java/util/Formatter.format;java/util/Formatter.format;itable stub 3
    """.trimIndent().lines()

    private val samples by lazy { real.mapNotNull(FlameGraph::parse) }

    @Test
    fun `parses a line, including frame names with spaces`() {
        val s = FlameGraph.parse("a;b;itable stub 3")
        assertThat(s).isEqualTo(Sample(listOf("a", "b", "itable stub"), 3))
        assertThat(FlameGraph.parse("   ")).isNull()
        assertThat(samples).hasSize(7)
        assertThat(samples.sumOf { it.count }).isEqualTo(1_243)
    }

    @Test
    fun `self time goes to the top frame only`() {
        val self = FlameGraph.selfTime(samples)
        assertThat(self["java/util/regex/Pattern.compile"]).isEqualTo(645)
        assertThat(self["java/util/Formatter.format"]).isEqualTo(169)
        assertThat(self["itable stub"]).isEqualTo(3)
        assertThat(self["PaymentSim.feeSlow"]).isNull()                // never on top in these samples
        assertThat(self.values.sum()).isEqualTo(1_243)
    }

    @Test
    fun `inclusive time counts a frame once per sample, even when it repeats in the stack`() {
        val incl = FlameGraph.inclusiveTime(samples)
        assertThat(incl["PaymentSim.feeSlow"]).isEqualTo(1_037)
        assertThat(incl["java/util/regex/Pattern.compile"]).`as`("Pattern.compile appears twice in one stack").isEqualTo(645)
        assertThat(incl["java/util/Formatter.format"]).isEqualTo(172)
        assertThat(incl["java/util/regex/Matcher.<init>"]).isEqualTo(220)
    }

    @Test
    fun `build merges equal prefixes into one box and sorts children alphabetically`() {
        val root = FlameGraph.build(samples)
        assertThat(root.name).isEqualTo("all")
        assertThat(root.total).isEqualTo(1_243)
        val lambda = root.children.single()
        val feeSlow = lambda.children.first()
        assertThat(lambda.children.map { it.name }).containsExactly("PaymentSim.feeSlow", "os::javaTimeNanos")
        assertThat(feeSlow.total).isEqualTo(1_037)
        assertThat(feeSlow.self).isZero()
        assertThat(feeSlow.children.map { it.name }).containsExactly(
            "java/lang/String.format", "java/util/regex/Pattern.compile", "java/util/regex/Pattern.matcher")
        assertThat(feeSlow.children.map { it.total }).containsExactly(172L, 645L, 220L)
        val outerFormat = feeSlow.children[0].children.single()
        val innerFormat = outerFormat.children.single()
        assertThat(outerFormat.total).isEqualTo(172)
        assertThat(innerFormat.self).`as`("91 + 78 merged, minus the 3 in itable stub").isEqualTo(169)
    }

    @Test
    fun `the hottest path follows the widest box at every level`() {
        assertThat(FlameGraph.hottestPath(FlameGraph.build(samples))).containsExactly(
            "PaymentSim.lambda\$main\$0", "PaymentSim.feeSlow", "java/util/regex/Pattern.compile",
            "java/util/regex/Pattern.<init>", "java/util/regex/Pattern.compile")
    }
}
