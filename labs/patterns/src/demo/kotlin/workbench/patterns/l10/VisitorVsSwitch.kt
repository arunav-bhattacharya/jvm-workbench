package workbench.patterns.l10

// The same expression tree evaluated with a classic Visitor and with a sealed when.

interface ExprVisitor<R> {
    fun visitNum(n: Num): R
    fun visitAdd(a: Add): R
    fun visitMul(m: Mul): R
}

sealed interface Expr { fun <R> accept(v: ExprVisitor<R>): R }
data class Num(val value: Int) : Expr { override fun <R> accept(v: ExprVisitor<R>) = v.visitNum(this) }
data class Add(val l: Expr, val r: Expr) : Expr { override fun <R> accept(v: ExprVisitor<R>) = v.visitAdd(this) }
data class Mul(val l: Expr, val r: Expr) : Expr { override fun <R> accept(v: ExprVisitor<R>) = v.visitMul(this) }

// operation 1, visitor style: one class per operation, one method per case
object Eval : ExprVisitor<Int> {
    override fun visitNum(n: Num) = n.value
    override fun visitAdd(a: Add) = a.l.accept(this) + a.r.accept(this)
    override fun visitMul(m: Mul) = m.l.accept(this) * m.r.accept(this)
}

// operation 1 again, data style: no accept needed, no visitor interface
private fun eval(e: Expr): Int = when (e) {
    is Num -> e.value
    is Add -> eval(e.l) + eval(e.r)
    is Mul if e.l == Num(0) -> 0                     // no nested patterns in Kotlin: a guard says it
    is Mul -> eval(e.l) * eval(e.r)
}

// operation 2: just one more function
private fun show(e: Expr): String = when (e) {
    is Num -> e.value.toString()
    is Add -> "(${show(e.l)} + ${show(e.r)})"
    is Mul -> "${show(e.l)} * ${show(e.r)}"
}

fun main() {
    val e = Add(Num(2), Mul(Num(3), Num(4)))
    println("${show(e)} = ${e.accept(Eval)} (visitor) = ${eval(e)} (when)")
    val zero = Mul(Num(0), e)
    println("${show(zero)} = ${eval(zero)}")
}
