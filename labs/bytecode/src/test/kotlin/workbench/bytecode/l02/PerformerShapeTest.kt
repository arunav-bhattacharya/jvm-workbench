package workbench.bytecode.l02

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException
import java.lang.reflect.Method
import java.lang.reflect.Modifier

/** Reads Performer's JVM shape with reflection: the members javap -p would list. */
class PerformerShapeTest {
    private val performer = Performer::class.java

    private fun publicMethod(name: String, vararg params: Class<*>): Method? =
        performer.methods.firstOrNull { it.name == name && it.parameterTypes.contentEquals(params) }

    @Test
    fun `Java can read Performer MAX_SHOWS as a public static final field`() {
        val f = performer.getField("MAX_SHOWS")
        assertThat(Modifier.isStatic(f.modifiers) && Modifier.isFinal(f.modifiers)).isTrue()
        assertThat(f.getInt(null)).isEqualTo(8)
    }

    @Test
    fun `Java can call Performer sign as a static method`() {
        val sign = publicMethod("sign", String::class.java)
        assertThat(sign).describedAs("public method Performer.sign(String)").isNotNull()
        assertThat(Modifier.isStatic(sign!!.modifiers)).describedAs("sign is static").isTrue()
        val p = sign.invoke(null, "ana") as Performer
        assertThat(p.name).isEqualTo("ana")
    }

    @Test
    fun `Java can call book with only the number of shows`() {
        val book = publicMethod("book", Int::class.javaPrimitiveType!!)
        assertThat(book).describedAs("public method book(int)").isNotNull()
        val p = Performer("ana")
        assertThat(book!!.invoke(p, 2)).isEqualTo(2)
        assertThat(book.invoke(p, 3)).isEqualTo(5)
    }

    @Test
    fun `shows has a public getter and no public setter`() {
        assertThat(publicMethod("getShows")).isNotNull()
        assertThat(performer.methods.map { it.name }).doesNotContain("setShows")
    }

    @Test
    fun `the resting flag reads as isResting and writes as setResting`() {
        val isResting = publicMethod("isResting")
        val setResting = publicMethod("setResting", Boolean::class.javaPrimitiveType!!)
        assertThat(isResting).describedAs("public boolean isResting()").isNotNull()
        assertThat(setResting).describedAs("public void setResting(boolean)").isNotNull()
        assertThat(performer.methods.map { it.name }).doesNotContain("getResting")
        val p = Performer("bo")
        setResting!!.invoke(p, true)
        assertThat(isResting!!.invoke(p)).isEqualTo(true)
    }

    @Test
    fun `exportCsv declares IOException so Java code can catch it`() {
        val export = publicMethod("exportCsv", Appendable::class.java)
        assertThat(export).isNotNull()
        assertThat(export!!.exceptionTypes).contains(IOException::class.java)
    }

    @Test
    fun `kotlinc checks non-null parameters at the door, whatever you change`() {
        // every public function with a non-null reference parameter starts with
        // Intrinsics.checkNotNullParameter, so Java passing null fails fast with the parameter's name
        val ctor = performer.getConstructor(String::class.java)
        val e = runCatching { ctor.newInstance(null) }.exceptionOrNull()?.cause
        assertThat(e).isInstanceOf(NullPointerException::class.java).hasMessageContaining("name")
    }
}
