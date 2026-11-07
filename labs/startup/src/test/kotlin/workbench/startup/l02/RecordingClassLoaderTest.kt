package workbench.startup.l02

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

private const val FIXTURES = "workbench.startup.l02.fixtures."

class RecordingClassLoaderTest {
    // every test gets a fresh loader, so nothing is defined in it yet
    private val loader = RecordingClassLoader(RecordingClassLoaderTest::class.java.classLoader, FIXTURES)

    @Test
    fun `loading a class without initializing it defines only that class`() {
        Class.forName(FIXTURES + "FeeTable", false, loader)
        assertThat(loader.defined()).containsExactly(FIXTURES + "FeeTable")
    }

    @Test
    fun `initializing a class also defines what its static initializer touches`() {
        Class.forName(FIXTURES + "FeeTable", true, loader)
        assertThat(loader.defined()).containsExactlyInAnyOrder(FIXTURES + "FeeTable", FIXTURES + "FeeRules")
    }

    @Test
    fun `the class is the loader's own copy, not the parent's`() {
        val mine = Class.forName(FIXTURES + "FeeTable", false, loader)
        val parents = Class.forName(FIXTURES + "FeeTable", false, RecordingClassLoaderTest::class.java.classLoader)
        assertThat(mine.classLoader).isSameAs(loader)
        assertThat(mine).isNotSameAs(parents)
    }

    @Test
    fun `classes outside the prefix come from the parent and are not recorded`() {
        assertThat(loader.loadClass("java.lang.String")).isSameAs(String::class.java)
        assertThat(loader.loadClass("workbench.startup.l02.TrainingRun")).isSameAs(TrainingRun::class.java)
        assertThat(loader.defined()).isEmpty()
    }

    @Test
    fun `asking twice gives the same class, recorded once`() {
        val first = loader.loadClass(FIXTURES + "Money")
        val second = loader.loadClass(FIXTURES + "Money")
        assertThat(first).isSameAs(second)
        assertThat(loader.defined()).containsExactly(FIXTURES + "Money")
    }

    @Test
    fun `a missing class inside the prefix throws ClassNotFoundException`() {
        assertThatThrownBy { loader.loadClass(FIXTURES + "NoSuchClass") }
            .isInstanceOf(ClassNotFoundException::class.java)
        assertThat(loader.defined()).isEmpty()
    }
}
