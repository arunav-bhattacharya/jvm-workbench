package workbench.injector.l03

import com.google.devtools.ksp.processing.KSPLogger
import com.google.devtools.ksp.symbol.KSNode
import com.google.devtools.ksp.symbol.KSType

// Given code: lesson 2's graph checks, unchanged. A Lazy or () -> T request is an edge like any other here.

/**
 * The night-before checks. [provided] holds every @Provides function of every @Module; a type nobody provides
 * there is built from its @Inject constructor, if it has one (and no qualifier was asked for). Every problem
 * goes to [error], on the exact symbol, and the checks carry on, so one build reports them all.
 */
class Graph(private val logger: KSPLogger, provided: List<ProvidesBinding>) {

    private val byKey: Map<Key, List<ProvidesBinding>> = provided.groupBy { it.key }

    /** How many problems were reported so far. A component whose checks added any is not written. */
    var errors = 0
        private set

    /** Given: reports one problem on [node] (its file and line). */
    fun error(message: String, node: KSNode) {
        logger.error(message, node)
        errors++
    }

    /** Given: the binding that answers [key], or null when nobody provides it. */
    fun bindingFor(key: Key, type: KSType): Binding? =
        byKey[key]?.first() ?: if (key.qualifier == null) constructorBinding(type) else null

    /** Given: the end of a missing-binding message, for a plain type or a qualified one. */
    fun hint(key: Key): String =
        if (key.qualifier != null) "Add a @Provides function with @Named(\"${key.qualifier}\") to a @Module."
        else "Add @Inject to its constructor, or a @Provides function in a @Module."

    /**
     * Two bindings for one key. For each key with more than one binding (two @Provides functions, or a
     * @Provides function for a class that also has an @Inject constructor), report every binding after the
     * first, on that binding's own declaration:
     *
     *     Route is provided twice: by RouteModule.highway() and by RouteModule.backRoads().
     *     Give each one its own @Named qualifier and ask for the one you mean.
     *
     * The @Inject constructor, when there is one, counts as the first.
     */
    fun checkDuplicates() {
        for ((key, functions) in byKey) {
            val constructor = if (key.qualifier == null) constructorBinding(functions.first().type) else null
            val all: List<Binding> = listOfNotNull(constructor) + functions
            for (second in all.drop(1)) {
                error(
                    "$key is provided twice: by ${all.first().origin} and by ${second.origin}. " +
                        "Give each one its own @Named qualifier and ask for the one you mean.",
                    second.node,
                )
            }
        }
    }

    /**
     * The walk from lesson 1, with a memory of the path it is on. Depth first from each entry point; a binding
     * joins the result when the walk leaves it (post-order), once. For each dependency of the binding you are in:
     *  - nobody provides it: report on the dependency's node, naming the whole path from the entry point's type,
     *        "MovingDay needs Crew needs Truck needs Driver: nobody provides Driver. " + hint(key)
     *    (for an entry point itself: "MovingDayComponent.helicopter() needs Helicopter: nobody provides ...");
     *  - it is already in the result: nothing to do, it is shared;
     *  - it is on the current path: a cycle; report on the dependency's node, from the repeated binding,
     *        "Dependency cycle: Truck needs Driver needs Truck. Nothing in a cycle can be built first: change one of these constructors."
     *  - otherwise: visit it.
     * Report and carry on: the result may be incomplete when [errors] went up.
     */
    fun creationOrder(entryPoints: List<EntryPoint>): List<Binding> {
        val done = LinkedHashMap<Key, Binding>()   // finished bindings, in creation order
        val path = ArrayList<Binding>()            // the bindings the walk is inside, outermost first

        fun visit(binding: Binding) {
            path += binding
            for (dependency in binding.dependencies) {
                val target = bindingFor(dependency.key, dependency.type)
                when {
                    target == null -> error(
                        (path + dependency.key).joinToString(" needs ") +
                            ": nobody provides ${dependency.key}. ${hint(dependency.key)}",
                        dependency.node,
                    )
                    target.key in done -> Unit                                   // already built: shared
                    path.any { it.key == target.key } -> {                       // we are inside it already
                        val loop = path.dropWhile { it.key != target.key } + target
                        error(
                            "Dependency cycle: ${loop.joinToString(" needs ")}. " +
                                "Nothing in a cycle can be built first: change one of these constructors.",
                            dependency.node,
                        )
                    }
                    else -> visit(target)
                }
            }
            path.removeAt(path.lastIndex)
            done[binding.key] = binding                                          // post-order
        }

        for (entry in entryPoints) {
            val target = bindingFor(entry.key, entry.type)
            when {
                target == null -> error("${entry.name} needs ${entry.key}: nobody provides ${entry.key}. ${hint(entry.key)}", entry.function)
                target.key !in done -> visit(target)
            }
        }
        return done.values.toList()
    }
}
