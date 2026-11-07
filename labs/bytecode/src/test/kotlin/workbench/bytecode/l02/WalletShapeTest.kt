package workbench.bytecode.l02

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException
import java.lang.reflect.Method
import java.lang.reflect.Modifier

/** Reads Wallet's JVM shape with reflection: the members javap -p would list. */
class WalletShapeTest {
    private val wallet = Wallet::class.java

    private fun publicMethod(name: String, vararg params: Class<*>): Method? =
        wallet.methods.firstOrNull { it.name == name && it.parameterTypes.contentEquals(params) }

    @Test
    fun `Java can read Wallet MAX_BALANCE_MINOR as a public static final field`() {
        val f = wallet.getField("MAX_BALANCE_MINOR")
        assertThat(Modifier.isStatic(f.modifiers) && Modifier.isFinal(f.modifiers)).isTrue()
        assertThat(f.getLong(null)).isEqualTo(10_000_000L)
    }

    @Test
    fun `Java can call Wallet open as a static method`() {
        val open = publicMethod("open", String::class.java)
        assertThat(open).describedAs("public method Wallet.open(String)").isNotNull()
        assertThat(Modifier.isStatic(open!!.modifiers)).describedAs("open is static").isTrue()
        val w = open.invoke(null, "ana") as Wallet
        assertThat(w.owner).isEqualTo("ana")
    }

    @Test
    fun `Java can call deposit with only the amount`() {
        val deposit = publicMethod("deposit", Long::class.javaPrimitiveType!!)
        assertThat(deposit).describedAs("public method deposit(long)").isNotNull()
        val w = Wallet("ana")
        assertThat(deposit!!.invoke(w, 1_250L)).isEqualTo(1_250L)
        assertThat(deposit.invoke(w, 750L)).isEqualTo(2_000L)
    }

    @Test
    fun `balanceMinor has a public getter and no public setter`() {
        assertThat(publicMethod("getBalanceMinor")).isNotNull()
        assertThat(wallet.methods.map { it.name }).doesNotContain("setBalanceMinor")
    }

    @Test
    fun `the frozen flag reads as isFrozen and writes as setFrozen`() {
        val isFrozen = publicMethod("isFrozen")
        val setFrozen = publicMethod("setFrozen", Boolean::class.javaPrimitiveType!!)
        assertThat(isFrozen).describedAs("public boolean isFrozen()").isNotNull()
        assertThat(setFrozen).describedAs("public void setFrozen(boolean)").isNotNull()
        assertThat(wallet.methods.map { it.name }).doesNotContain("getFrozen")
        val w = Wallet("bo")
        setFrozen!!.invoke(w, true)
        assertThat(isFrozen!!.invoke(w)).isEqualTo(true)
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
        val ctor = wallet.getConstructor(String::class.java)
        val e = runCatching { ctor.newInstance(null) }.exceptionOrNull()?.cause
        assertThat(e).isInstanceOf(NullPointerException::class.java).hasMessageContaining("owner")
    }
}
