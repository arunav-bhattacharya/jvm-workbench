package workbench.memory.l06

object GcLog {
    // GC(22)  y:  Pause Young  (Prepare Mixed) (G1 Evacuation Pause)  996M->760M(1024M)  43.391ms
    private val PAUSE = Regex(
        """GC\((\d+)\) (?:[yYO]: )?(Pause(?: [A-Z]\w*)+)""" +   // id, generation prefix, kind
        """((?: \((?:[^()]|\(\))*\))*)""" +                      // labels; "(System.gc())" has parentheses inside
        """(?: (\d+)M->(\d+)M\((\d+)M\))?""" +                    // heap before -> after (committed), if present
        """ ([\d.]+)ms$"""                                         // the pause itself, at the very end
    )
    private val LABEL = Regex("""\(((?:[^()]|\(\))*)\)""")

    fun parsePause(line: String): GcPause? {
        val m = PAUSE.find(line.trimEnd()) ?: return null
        val (id, kind, labels, before, after, committed, ms) = m.destructured
        return GcPause(
            gcId = id.toInt(),
            kind = kind,
            labels = LABEL.findAll(labels).map { it.groupValues[1] }.toList(),
            heapBeforeMb = before.toIntOrNull(),
            heapAfterMb = after.toIntOrNull(),
            heapCommittedMb = committed.toIntOrNull(),
            millis = ms.toDouble(),
        )
    }

    fun summarize(lines: List<String>): PauseSummary {
        val pauses = lines.mapNotNull(::parsePause)
        val fulls = pauses.filter { it.kind == "Pause Full" }
        return PauseSummary(
            pauses = pauses.size,
            totalMillis = pauses.sumOf { it.millis },
            longestMillis = pauses.maxOfOrNull { it.millis } ?: 0.0,
            fullGcs = fulls.size,
            evacuationFailures = pauses.count { "Evacuation Failure" in it.labels },
            liveAfterLastFullMb = fulls.lastOrNull()?.heapAfterMb,
        )
    }
}
