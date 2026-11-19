package workbench.ksp.app.smoke

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

// Smoke example (keep or delete): calls code that KSP generated in a real Gradle build.
class GreeterTest {

    @Test
    fun `the generated function is ordinary code the app calls`() {
        assertThat(helloFromGreeter()).isEqualTo("Hello from Greeter")
        assertThat(Greeter().greet()).isEqualTo("Hello from Greeter!")
    }
}
