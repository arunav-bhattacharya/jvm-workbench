package workbench.generics.l07

/**
 * Renders any map for the shop log: entries as `key=value`, sorted by the key's toString(), joined
 * with ", " and wrapped in braces. A value that is itself a map is rendered the same way.
 *
 *     render(mapOf("lemon" to 120, "apple" to 180))                == "{apple=180, lemon=120}"
 *     render(mapOf("crates" to 4, "apple" to mapOf("name" to "Gala")))
 *                                                                    == "{apple={name=Gala}, crates=4}"
 *     render(mapOf("note" to null))                                  == "{note=null}"
 *     render(emptyMap<String, Int>())                                == "{}"
 *
 * Keys and values of a Map<*, *> are read as Any?.
 */
fun render(map: Map<*, *>): String =
    TODO("sort the entries by key.toString(), render nested Map<*, *> values recursively")
