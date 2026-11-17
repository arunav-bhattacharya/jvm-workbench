package workbench.performance.l01

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class PrintCompilationTest {

    // real output of Hot.java on JDK 21.0.12, trimmed to a few of the JDK's own lines, the lines for
    // longLoop, Paragraph::millis and readingMillis, and the program's output
    private val jdk21 = """
        69    3     n 0       jdk.internal.misc.Unsafe::getReferenceVolatile (native)   
        69    1       3       java.lang.Object::<init> (1 bytes)
        76    8 %     3       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)
        76    9       3       workbench.performance.l01.Hot::longLoop (27 bytes)
        76   10 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)
        79    8 %     3       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant
        240   10 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant
        1251976370825152
        241   11     n 0       java.lang.System::arraycopy (native)   (static)
        242   14       3       workbench.performance.l01.Hot${'$'}Paragraph::millis (9 bytes)
        242   15       4       workbench.performance.l01.Hot${'$'}Paragraph::millis (9 bytes)
        242   14       3       workbench.performance.l01.Hot${'$'}Paragraph::millis (9 bytes)   made not entrant
        245   16 %     3       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)
        245   17       3       workbench.performance.l01.Hot::readingMillis (42 bytes)
        245   18 %     4       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)
        253   16 %     3       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)   made not entrant
        253   19       4       workbench.performance.l01.Hot::readingMillis (42 bytes)
        255   17       3       workbench.performance.l01.Hot::readingMillis (42 bytes)   made not entrant
        296   18 %     4       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)   made not entrant
        296   19       4       workbench.performance.l01.Hot::readingMillis (42 bytes)   made not entrant
        296   24 %     3       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)
        296   25       3       workbench.performance.l01.Hot::readingMillis (42 bytes)
        297   28 %     4       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)
        299   24 %     3       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)   made not entrant
        299   29       4       workbench.performance.l01.Hot::readingMillis (42 bytes)
        304   25       3       workbench.performance.l01.Hot::readingMillis (42 bytes)   made not entrant
        5661666000000
    """.trimIndent().lines()

    // real output of the same program on JDK 25.0.5, trimmed the same way: the reason follows a colon
    private val jdk25 = """
        55   11 %     3       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)
        55   12       3       workbench.performance.l01.Hot::longLoop (27 bytes)
        56   13 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)
        67   11 %     3       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant: OSR invalidation of lower level
        246   13 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant: uncommon trap
        252   19       2       workbench.performance.l01.Hot${'$'}Paragraph::millis (9 bytes)
        252   20       4       workbench.performance.l01.Hot${'$'}Paragraph::millis (9 bytes)
        252   19       2       workbench.performance.l01.Hot${'$'}Paragraph::millis (9 bytes)   made not entrant: not used
        254   21 %     3       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)
        257   22       3       workbench.performance.l01.Hot::readingMillis (42 bytes)
        257   23 %     4       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)
        260   21 %     3       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)   made not entrant: OSR invalidation of lower level
        271   24       4       workbench.performance.l01.Hot::readingMillis (42 bytes)
        274   22       3       workbench.performance.l01.Hot::readingMillis (42 bytes)   made not entrant: not used
        309   23 %     4       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)   made not entrant: uncommon trap
        309   24       4       workbench.performance.l01.Hot::readingMillis (42 bytes)   made not entrant: uncommon trap
        312   30 %     3       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)
        314   33       3       workbench.performance.l01.Hot::readingMillis (42 bytes)
        317   34 %     4       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)
        325   30 %     3       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)   made not entrant: OSR invalidation of lower level
        327   35       4       workbench.performance.l01.Hot::readingMillis (42 bytes)
        328   33       3       workbench.performance.l01.Hot::readingMillis (42 bytes)   made not entrant: not used
    """.trimIndent().lines()

    @Test
    fun `parses a plain C1 line`() {
        val e = PrintCompilation.parse("76    9       3       workbench.performance.l01.Hot::longLoop (27 bytes)")
        assertThat(e).isEqualTo(
            CompileEvent(
                millis = 76, compileId = 9, osr = false, synchronized = false, exceptionHandler = false,
                native = false, tier = 3, method = "workbench.performance.l01.Hot::longLoop", osrBci = null,
                bytes = 27, madeNotEntrant = false, reason = null,
            )
        )
    }

    @Test
    fun `parses an OSR line with its loop bytecode index`() {
        val e = PrintCompilation.parse("76   10 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)")!!
        assertThat(e.osr).isTrue()
        assertThat(e.tier).isEqualTo(4)
        assertThat(e.osrBci).isEqualTo(4)
        assertThat(e.method).isEqualTo("workbench.performance.l01.Hot::longLoop")
        assertThat(e.bytes).isEqualTo(27)
    }

    @Test
    fun `reads the attribute characters and native methods`() {
        val native = PrintCompilation.parse("69    3     n 0       jdk.internal.misc.Unsafe::getReferenceVolatile (native)   ")!!
        assertThat(native.native).isTrue()
        assertThat(native.tier).isEqualTo(0)
        assertThat(native.bytes).isNull()
        assertThat(native.method).isEqualTo("jdk.internal.misc.Unsafe::getReferenceVolatile")

        val sync = PrintCompilation.parse("58   25  s    3       Flags::syncInc (9 bytes)")!!
        assertThat(sync.synchronized).isTrue()
        assertThat(sync.exceptionHandler).isFalse()

        val handler = PrintCompilation.parse("59   27   !   3       Flags::parse (8 bytes)")!!
        assertThat(handler.exceptionHandler).isTrue()
        assertThat(handler.synchronized).isFalse()
    }

    @Test
    fun `reads made not entrant with and without a JDK 25 reason`() {
        val old = PrintCompilation.parse("240   10 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant")!!
        assertThat(old.madeNotEntrant).isTrue()
        assertThat(old.reason).isNull()
        assertThat(old.compileId).isEqualTo(10)

        val new = PrintCompilation.parse("309   24       4       workbench.performance.l01.Hot::readingMillis (42 bytes)   made not entrant: uncommon trap")!!
        assertThat(new.madeNotEntrant).isTrue()
        assertThat(new.reason).isEqualTo("uncommon trap")
        assertThat(new.bytes).isEqualTo(42)
    }

    @Test
    fun `parses lines with no tier column when tiered compilation is off`() {
        val e = PrintCompilation.parse("103    2 %           Hot::longLoop @ 4 (27 bytes)")!!
        assertThat(e.tier).isNull()
        assertThat(e.osr).isTrue()
        assertThat(e.method).isEqualTo("Hot::longLoop")
    }

    @Test
    fun `ignores program output and other noise`() {
        assertThat(PrintCompilation.parse("1251976370825152")).isNull()
        assertThat(PrintCompilation.parse("")).isNull()
        assertThat(PrintCompilation.parse("Picked up JAVA_TOOL_OPTIONS: -Xmx1g")).isNull()
        assertThat(PrintCompilation.parseAll(jdk21)).hasSize(25)
    }

    @Test
    fun `finds the methods still running in C2 at the end`() {
        assertThat(PrintCompilation.runningInC2(PrintCompilation.parseAll(jdk21)))
            .containsExactlyInAnyOrder("workbench.performance.l01.Hot\$Paragraph::millis", "workbench.performance.l01.Hot::readingMillis")
        assertThat(PrintCompilation.runningInC2(PrintCompilation.parseAll(jdk25)))
            .containsExactlyInAnyOrder("workbench.performance.l01.Hot\$Paragraph::millis", "workbench.performance.l01.Hot::readingMillis")
    }

    @Test
    fun `finds the methods whose C2 code was thrown away`() {
        val expected = arrayOf("workbench.performance.l01.Hot::longLoop", "workbench.performance.l01.Hot::readingMillis")
        assertThat(PrintCompilation.deoptimizedFromC2(PrintCompilation.parseAll(jdk21))).containsExactlyInAnyOrder(*expected)
        assertThat(PrintCompilation.deoptimizedFromC2(PrintCompilation.parseAll(jdk25))).containsExactlyInAnyOrder(*expected)
    }
}
