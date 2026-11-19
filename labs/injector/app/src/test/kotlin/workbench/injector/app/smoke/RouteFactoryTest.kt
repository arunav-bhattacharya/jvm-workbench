package workbench.injector.app.smoke

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

// Smoke example (keep or delete): calls the factory KSP generated in a real Gradle build.
class RouteFactoryTest {

    @Test
    fun `the generated factory builds a new route each time`() {
        val first = RouteFactory.create()
        assertThat(first.name).isEqualTo("highway")
        assertThat(RouteFactory.create()).isNotSameAs(first)
    }
}
