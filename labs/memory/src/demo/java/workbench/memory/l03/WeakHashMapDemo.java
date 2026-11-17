package workbench.memory.l03;

import java.util.Map;
import java.util.WeakHashMap;

/** WeakHashMap drops an entry when its key is unreachable, unless the value refers to the key. */
public class WeakHashMapDemo {
    record Photo(String name) {}
    record Preview(int width) {}                                   // knows nothing about its photo
    record Thumbnail(Photo source, int width) {}                   // refers back to its own key

    public static void main(String[] args) throws InterruptedException {
        Map<Photo, Preview> previews = new WeakHashMap<>();
        Map<Photo, Thumbnail> thumbnails = new WeakHashMap<>();
        Photo beach = new Photo("beach.jpg");
        Photo dog = new Photo("dog.jpg");
        previews.put(beach, new Preview(160));
        thumbnails.put(dog, new Thumbnail(dog, 160));

        beach = null;                                              // the photos are deleted: nothing else refers to them
        dog = null;
        for (int i = 0; i < 5; i++) { System.gc(); Thread.sleep(20); }   // demo only: ask for a few GCs

        System.out.println("previews left:   " + previews.size());       // size() also removes cleared entries
        System.out.println("thumbnails left: " + thumbnails.size());
    }
}
