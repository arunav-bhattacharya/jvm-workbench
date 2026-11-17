package workbench.generics.l05

class DeliveryBell<E> {
    private val listeners = ArrayList<(E) -> Unit>()

    fun listen(listener: (E) -> Unit) {
        listeners.add(listener)   // a (Fruit) -> Unit is already an (Apple) -> Unit
    }

    fun ring(item: E): Int {
        for (l in listeners) l(item)
        return listeners.size
    }
}
