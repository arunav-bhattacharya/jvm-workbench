package workbench.generics.l03

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class SubtypingTest {
    // a small world of classes, wired the way Kotlin wires them
    private val any = Klass("Any")
    private val comparable = Klass("Comparable", listOf(any))     // its type parameter is left out of this model
    private val charSequence = Klass("CharSequence", listOf(any))
    private val string = Klass("String", listOf(charSequence, comparable))
    private val number = Klass("Number", listOf(any))
    private val int = Klass("Int", listOf(number, comparable))
    private val payment = Klass("Payment", listOf(any))
    private val cardPayment = Klass("CardPayment", listOf(payment))
    private val list = Klass("List", listOf(any), covariant = true)    // List<out E>
    private val mutableList = Klass("MutableList", listOf(list))       // MutableList<E>, invariant
    private val arrayList = Klass("ArrayList", listOf(mutableList))

    private fun t(k: Klass, vararg args: Type) = Type(k, args.toList())
    private fun Type.orNull() = copy(nullable = true)
    private infix fun Type.isA(sup: Type) = isSubtype(this, sup)

    @Test
    fun `isSubclass follows inheritance through several hops`() {
        assertThat(isSubclass(string, string)).isTrue()
        assertThat(isSubclass(string, charSequence)).isTrue()
        assertThat(isSubclass(string, any)).isTrue()
        assertThat(isSubclass(arrayList, list)).isTrue()
        assertThat(isSubclass(any, string)).isFalse()
        assertThat(isSubclass(int, charSequence)).isFalse()
    }

    @Test
    fun `one class, two types - String fits where String-or-null is expected, not the reverse`() {
        assertThat(t(string) isA t(string).orNull()).isTrue()
        assertThat(t(string).orNull() isA t(string)).isFalse()
        assertThat(t(string).orNull() isA t(any).orNull()).isTrue()
        assertThat(t(string).orNull() isA t(any)).isFalse()
        assertThat(t(string) isA t(any).orNull()).isTrue()
    }

    @Test
    fun `plain classes - a subclass is a subtype`() {
        assertThat(t(cardPayment) isA t(payment)).isTrue()
        assertThat(t(payment) isA t(cardPayment)).isFalse()
        assertThat(t(int) isA t(string)).isFalse()
    }

    @Test
    fun `MutableList is invariant - MutableList of String is not a MutableList of Any`() {
        assertThat(t(mutableList, t(string)) isA t(mutableList, t(string))).isTrue()
        assertThat(t(mutableList, t(string)) isA t(mutableList, t(any))).isFalse()
        assertThat(t(mutableList, t(cardPayment)) isA t(mutableList, t(payment))).isFalse()
        assertThat(t(mutableList, t(string)) isA t(mutableList, t(string).orNull())).isFalse()
    }

    @Test
    fun `a subclass passes its argument up - ArrayList of String is a MutableList of String`() {
        assertThat(t(arrayList, t(string)) isA t(mutableList, t(string))).isTrue()
        assertThat(t(arrayList, t(string)) isA t(mutableList, t(any))).isFalse()
        assertThat(t(arrayList, t(string)) isA t(any)).isTrue()
    }

    @Test
    fun `List is covariant - List of String is a List of Any`() {
        assertThat(t(list, t(string)) isA t(list, t(any))).isTrue()
        assertThat(t(list, t(any)) isA t(list, t(string))).isFalse()
        assertThat(t(list, t(string)) isA t(list, t(string).orNull())).isTrue()
        assertThat(t(list, t(string).orNull()) isA t(list, t(string))).isFalse()
        assertThat(t(mutableList, t(string)) isA t(list, t(any))).isTrue()     // read-only view of a mutable list
        assertThat(t(list, t(cardPayment)).orNull() isA t(list, t(payment)).orNull()).isTrue()
    }

    @Test
    fun `nested arguments - covariance composes, invariance anywhere blocks it`() {
        assertThat(t(list, t(list, t(string))) isA t(list, t(list, t(any)))).isTrue()
        assertThat(t(list, t(mutableList, t(string))) isA t(list, t(mutableList, t(any)))).isFalse()
        assertThat(t(mutableList, t(list, t(string))) isA t(mutableList, t(list, t(any)))).isFalse()
    }
}
