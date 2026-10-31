package workbench.concurrency.l03;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class SeatMap {
    private final Map<Integer, String> owners = new ConcurrentHashMap<>();

    public boolean book(int seat, String passenger) {
        priceTheSeat();
        // check and act in ONE atomic map call: only one thread can see null here
        return owners.putIfAbsent(seat, passenger) == null;
    }

    public String ownerOf(int seat) {
        return owners.get(seat);
    }

    private static void priceTheSeat() {
        for (int i = 0; i < 300; i++) Thread.onSpinWait();
    }
}
