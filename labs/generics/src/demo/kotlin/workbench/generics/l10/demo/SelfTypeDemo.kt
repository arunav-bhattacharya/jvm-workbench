package workbench.generics.l10.demo

// 1. Without a self type: the base setters return the base class, and the chain loses the subclass.
open class PlainBuilder {
    protected var cents = 0L
    fun amount(cents: Long): PlainBuilder { this.cents = cents; return this }
}
class PlainCardBuilder : PlainBuilder() {
    private var token = ""
    fun cardToken(t: String): PlainCardBuilder { token = t; return this }
    fun build() = "card $cents with $token"
}

// 2. With a self type: B names "my own subclass", so the base setters return it.
abstract class Builder<B : Builder<B>> {
    protected var cents = 0L
    fun amount(cents: Long): B { this.cents = cents; return self() }
    protected abstract fun self(): B
}
class CardBuilder : Builder<CardBuilder>() {
    private var token = ""
    fun cardToken(t: String): CardBuilder { token = t; return this }
    override fun self() = this
    fun build() = "card $cents with $token"
}

fun main() {
    println(PlainCardBuilder().cardToken("tok_1").amount(1_200))       // compiles, but the result is a PlainBuilder
    println(CardBuilder().amount(1_200).cardToken("tok_1").build())    // the chain keeps CardBuilder

    // Wrong moves. Uncomment one at a time, predict the error, then run.
    // println(PlainCardBuilder().amount(1_200).cardToken("tok_1").build())   // 1
    // class Liar : Builder<CardBuilder>() { override fun self() = CardBuilder() }   // 2 (compiles: what does it break?)
}
