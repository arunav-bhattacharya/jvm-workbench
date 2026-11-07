package workbench.performance.l06

data class Sample(val frames: List<String>, val count: Long)

object FlameGraph {

    fun parse(line: String): Sample? {
        if (line.isBlank()) return null
        val cut = line.lastIndexOf(' ')                       // frame names may contain spaces
        return Sample(line.substring(0, cut).split(';'), line.substring(cut + 1).trim().toLong())
    }

    fun selfTime(samples: List<Sample>): Map<String, Long> {
        val self = HashMap<String, Long>()
        for (s in samples) self.merge(s.frames.last(), s.count, Long::plus)
        return self
    }

    fun inclusiveTime(samples: List<Sample>): Map<String, Long> {
        val inclusive = HashMap<String, Long>()
        for (s in samples) {
            for (frame in s.frames.toSet()) inclusive.merge(frame, s.count, Long::plus)   // once per sample
        }
        return inclusive
    }

    fun build(samples: List<Sample>): FlameNode {
        val root = FlameNode("all")
        for (s in samples) {
            root.total += s.count
            var node = root
            for (frame in s.frames) {                         // same prefix, same boxes: that's the merge
                node = node.child(frame)
                node.total += s.count
            }
        }
        return root
    }

    fun hottestPath(root: FlameNode): List<String> {
        val path = mutableListOf<String>()
        var node = root
        while (node.children.isNotEmpty()) {
            node = node.children.maxBy { it.total }
            path += node.name
        }
        return path
    }
}
