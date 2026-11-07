package workbench.generics.l07

/**
 * Renders any map for a log line: entries as `key=value`, sorted by the key's toString(), joined
 * with ", " and wrapped in braces. A value that is itself a map is rendered the same way.
 *
 *     render(mapOf("USD" to 350, "EUR" to 1200))                    == "{EUR=1200, USD=350}"
 *     render(mapOf("card" to mapOf("scheme" to "visa"), "cents" to 99))
 *                                                                    == "{card={scheme=visa}, cents=99}"
 *     render(mapOf("note" to null))                                  == "{note=null}"
 *     render(emptyMap<String, Int>())                                == "{}"
 *
 * Keys and values of a Map<*, *> are read as Any?.
 */
fun render(map: Map<*, *>): String =
    TODO("sort the entries by key.toString(), render nested Map<*, *> values recursively")
