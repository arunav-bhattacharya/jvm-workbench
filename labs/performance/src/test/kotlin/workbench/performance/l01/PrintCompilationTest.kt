package workbench.performance.l01

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class PrintCompilationTest {

    // real output of Hot.java on JDK 21.0.12 (with the JDK's own lines and the program output mixed in)
    private val jdk21 = """
        32    1       3       java.lang.Object::<init> (1 bytes)
        34    3     n 0       jdk.internal.misc.Unsafe::getReferenceVolatile (native)
        40    8 %     3       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)
        40    9       3       workbench.performance.l01.Hot::longLoop (27 bytes)
        45   10 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)
        48    8 %     3       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant
        69   10 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant
        1251976370825152
        71   15       3       workbench.performance.l01.Hot${'$'}Square::area (10 bytes)
        71   16       4       workbench.performance.l01.Hot${'$'}Square::area (10 bytes)
        71   15       3       workbench.performance.l01.Hot${'$'}Square::area (10 bytes)   made not entrant
        72   17 %     3       workbench.performance.l01.Hot::total @ 11 (42 bytes)
        72   18       3       workbench.performance.l01.Hot::total (42 bytes)
        73   19 %     4       workbench.performance.l01.Hot::total @ 11 (42 bytes)
        77   20       4       workbench.performance.l01.Hot::total (42 bytes)
        93   19 %     4       workbench.performance.l01.Hot::total @ 11 (42 bytes)   made not entrant
        93   20       4       workbench.performance.l01.Hot::total (42 bytes)   made not entrant
        94   29       3       workbench.performance.l01.Hot::total (42 bytes)
        96   32       4       workbench.performance.l01.Hot::total (42 bytes)
        98   29       3       workbench.performance.l01.Hot::total (42 bytes)   made not entrant
        104   20     n 0       java.lang.System::arraycopy (native)   (static)
        1.6921637470390625E13
    """.trimIndent().lines()

    // real output of the same program on JDK 25 (Temurin 25+36): the reason follows a colon
    private val jdk25 = """
        23   14 %     3       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)
        23   16 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)
        25   14 %     3       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant: OSR invalidation of lower levels
        40   16 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant: uncommon trap
        41   22       2       workbench.performance.l01.Hot${'$'}Square::area (10 bytes)
        42   23       4       workbench.performance.l01.Hot${'$'}Square::area (10 bytes)
        42   22       2       workbench.performance.l01.Hot${'$'}Square::area (10 bytes)   made not entrant: not used
        47   27       4       workbench.performance.l01.Hot::total (42 bytes)
        60   27       4       workbench.performance.l01.Hot::total (42 bytes)   made not entrant: uncommon trap
        60   33       4       workbench.performance.l01.Hot::total (42 bytes)
    """.trimIndent().lines()

    @Test
    fun `parses a plain C1 line`() {
        val e = PrintCompilation.parse("40    9       3       workbench.performance.l01.Hot::longLoop (27 bytes)")
        assertThat(e).isEqualTo(
            CompileEvent(
                millis = 40, compileId = 9, osr = false, synchronized = false, exceptionHandler = false,
                native = false, tier = 3, method = "workbench.performance.l01.Hot::longLoop", osrBci = null,
                bytes = 27, madeNotEntrant = false, reason = null,
            )
        )
    }

    @Test
    fun `parses an OSR line with its loop bytecode index`() {
        val e = PrintCompilation.parse("45   10 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)")!!
        assertThat(e.osr).isTrue()
        assertThat(e.tier).isEqualTo(4)
        assertThat(e.osrBci).isEqualTo(4)
        assertThat(e.method).isEqualTo("workbench.performance.l01.Hot::longLoop")
        assertThat(e.bytes).isEqualTo(27)
    }

    @Test
    fun `reads the attribute characters and native methods`() {
        val native = PrintCompilation.parse("34    3     n 0       jdk.internal.misc.Unsafe::getReferenceVolatile (native)   ")!!
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
        val old = PrintCompilation.parse("69   10 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant")!!
        assertThat(old.madeNotEntrant).isTrue()
        assertThat(old.reason).isNull()
        assertThat(old.compileId).isEqualTo(10)

        val new = PrintCompilation.parse("60   27       4       workbench.performance.l01.Hot::total (42 bytes)   made not entrant: uncommon trap")!!
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
        assertThat(PrintCompilation.parseAll(jdk21)).hasSize(20)
    }

    @Test
    fun `finds the methods still running in C2 at the end`() {
        assertThat(PrintCompilation.runningInC2(PrintCompilation.parseAll(jdk21)))
            .containsExactlyInAnyOrder("workbench.performance.l01.Hot\$Square::area", "workbench.performance.l01.Hot::total")
        assertThat(PrintCompilation.runningInC2(PrintCompilation.parseAll(jdk25)))
            .containsExactlyInAnyOrder("workbench.performance.l01.Hot\$Square::area", "workbench.performance.l01.Hot::total")
    }

    @Test
    fun `finds the methods whose C2 code was thrown away`() {
        val expected = arrayOf("workbench.performance.l01.Hot::longLoop", "workbench.performance.l01.Hot::total")
        assertThat(PrintCompilation.deoptimizedFromC2(PrintCompilation.parseAll(jdk21))).containsExactlyInAnyOrder(*expected)
        assertThat(PrintCompilation.deoptimizedFromC2(PrintCompilation.parseAll(jdk25))).containsExactlyInAnyOrder(*expected)
    }
}
