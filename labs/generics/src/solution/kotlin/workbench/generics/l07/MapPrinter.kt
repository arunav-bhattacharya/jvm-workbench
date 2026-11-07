package workbench.generics.l07

fun render(map: Map<*, *>): String =
    map.entries
        .sortedBy { it.key.toString() }                       // keys are Any?: toString() works on null too
        .joinToString(", ", "{", "}") { (k, v) ->
            val shown = if (v is Map<*, *>) render(v) else v.toString()   // smart cast to Map<*, *>
            "$k=$shown"
        }
