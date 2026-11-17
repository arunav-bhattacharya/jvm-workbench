package workbench.kotlin.l06

import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.lang.reflect.Modifier

class PluginsTest {

    private val events = listOf(
        Queued("job-1", 12),
        Jammed("job-1", 7, "laser-1"),
        Printed("job-1", 12),
    )

    @Test
    fun `events survive a round trip through JSON`() {
        assertThat(decodeEvents(encodeEvents(events))).isEqualTo(events)
    }

    @Test
    fun `each element carries a stable type discriminator`() {
        val types = Json.parseToJsonElement(encodeEvents(events)).jsonArray
            .map { it.jsonObject["type"]!!.jsonPrimitive.content }
        assertThat(types).containsExactly("queued", "jammed", "printed")
    }

    @Test
    fun `defaults and nulls are left out of the JSON`() {
        val text = encodeEvents(listOf(Queued("job-2", 4), Jammed("job-2", 3)))
        assertThat(text).doesNotContain("paper").doesNotContain("printer").doesNotContain("null")
        assertThat(decodeEvents(text)).containsExactly(Queued("job-2", 4, "A4"), Jammed("job-2", 3, null))
    }

    @Test
    fun `an unknown event type fails, an unknown key is ignored`() {
        assertThatThrownBy { decodeEvents("""[{"type":"recycled","jobId":"job-3"}]""") }
            .isInstanceOf(SerializationException::class.java)
        assertThat(decodeEvents("""[{"type":"printed","jobId":"job-3","pages":1,"tray":"2"}]"""))
            .containsExactly(Printed("job-3", 1))
    }

    @Test
    fun `SheetPlanner is open, so a framework can generate a subclass proxy`() {
        val cls = SheetPlanner::class.java
        assertThat(Modifier.isFinal(cls.modifiers)).`as`("class SheetPlanner is final").isFalse()
        val sheets = cls.getMethod("sheetsFor", Int::class.javaPrimitiveType)
        assertThat(Modifier.isFinal(sheets.modifiers)).`as`("sheetsFor is final").isFalse()
        assertThat(SheetPlanner().sheetsFor(9)).isEqualTo(5)
    }

    @Test
    fun `JobRecord has a no-arg constructor for frameworks, and it skips the initializers`() {
        val cls = JobRecord::class.java
        assertThat(Modifier.isFinal(cls.modifiers)).`as`("class JobRecord is final").isFalse()
        val ctor = cls.getDeclaredConstructor()                    // what a database library looks up
        val blank = ctor.newInstance()
        // invokeInitializers is off (the default), so the non-null String property was never set
        val status = cls.getDeclaredField("status").apply { isAccessible = true }.get(blank)
        assertThat(status).isNull()
        assertThat(JobRecord("job-4", 10).status).isEqualTo("NEW")
    }
}
