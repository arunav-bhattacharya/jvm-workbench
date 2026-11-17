package workbench.bytecode.l07

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

class CallCountingAgentTest {
    private val play = "workbench.bytecode.l07.SoundBoard.play"
    private val check = "workbench.bytecode.l07.SoundBoard.check"
    private var installed: Installed? = null

    @BeforeEach
    fun reset() = CallCounts.reset()

    @AfterEach
    fun uninstall() {
        installed?.uninstall()
        installed = null
    }

    @Test
    fun `the agent can retransform classes that are already loaded`() {
        val inst = CallCountingAgent.instrumentation()
        assertThat(inst.isRetransformClassesSupported).isTrue()
        assertThat(inst.isModifiableClass(SoundBoard::class.java)).isTrue()
        assertThat(inst.allLoadedClasses).contains(SoundBoard::class.java)
    }

    @Test
    fun `an instance created before the agent was installed is counted afterwards`() {
        val board = SoundBoard()
        board.play("SQ-1")                                       // before: not counted
        installed = CallCountingAgent.countCalls(SoundBoard::class.java, "play")
        board.play("SQ-2")
        board.play("SQ-3")
        assertThat(CallCounts.of(play)).isEqualTo(2)
        assertThat(board.javaClass).isSameAs(SoundBoard::class.java)   // same class, new method body
    }

    @Test
    fun `only the matched method is counted`() {
        installed = CallCountingAgent.countCalls(SoundBoard::class.java, "play")
        SoundBoard().check("SQ-4")
        assertThat(CallCounts.of(check)).isZero()
    }

    @Test
    fun `calls a method makes on this are counted too, because the advice is inside the method`() {
        installed = CallCountingAgent.countCalls(SoundBoard::class.java, "play")
        assertThat(SoundBoard().playAll(listOf("SQ-5", "SQ-6", "SQ-7"))).isEqualTo(3)
        assertThat(CallCounts.of(play)).isEqualTo(3)
    }

    @Test
    fun `retransformation keeps static state and the method still does its work`() {
        SoundBoard().play("SQ-8")
        val before = SoundBoard.played
        installed = CallCountingAgent.countCalls(SoundBoard::class.java, "play")
        assertThat(SoundBoard().play("SQ-9")).isEqualTo("played SQ-9")
        assertThat(SoundBoard.played).isEqualTo(before + 1)              // no static initializer ran again
    }

    @Test
    fun `uninstalling restores the original method body`() {
        val board = SoundBoard()
        installed = CallCountingAgent.countCalls(SoundBoard::class.java, "play")
        board.play("SQ-10")
        installed!!.uninstall()
        installed = null
        board.play("SQ-11")
        assertThat(CallCounts.of(play)).isEqualTo(1)
    }
}
