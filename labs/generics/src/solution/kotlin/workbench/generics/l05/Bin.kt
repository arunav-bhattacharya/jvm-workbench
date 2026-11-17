package workbench.generics.l05

// in T: a Bin only takes T values in, so a Bin<Fruit> can safely act as a Bin<Apple>
interface Bin<in T> {
    fun drop(item: T)
}

// the class has to be invariant: `items` hands T back out, `drop` takes T in
class CollectingBin<T> : Bin<T> {
    private val dropped = ArrayList<T>()

    val items: List<T>
        get() = dropped.toList()   // a copy, so callers can't change what the bin remembers

    override fun drop(item: T) {
        dropped.add(item)
    }
}

fun dropAll(fruit: List<Fruit>, bin: Bin<Fruit>): Int {
    for (f in fruit) bin.drop(f)
    return fruit.size
}
