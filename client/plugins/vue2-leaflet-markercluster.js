import Vue from "vue";
import * as L from "leaflet";
import Vue2LeafletMarkerCluster from "vue2-leaflet-markercluster";
Vue.component("v-marker-cluster", Vue2LeafletMarkerCluster);

const LeafletPlugin = {
  install(Vue) {
    /*
    Fix Leaflet issue with lines between tiles
    https://github.com/Leaflet/Leaflet/issues/3575#issuecomment-150544739 */
    var originalInitTile = L.GridLayer.prototype._initTile
    L.GridLayer.include({
        _initTile: function (tile) {
            originalInitTile.call(this, tile);

            var tileSize = this.getTileSize();

            tile.style.width = tileSize.x + 1 + 'px';
            tile.style.height = tileSize.y + 1 + 'px';
        }
    });
    // Expose Leaflet
    Vue.prototype.$L = L;
  }
};

Vue.use(LeafletPlugin);