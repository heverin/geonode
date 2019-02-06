import getRequestQueue from "app/search/functions/getRequestQueue";
import requestMultiple from "app/search/functions/requestMultiple";
import activateSidebarToggle from "app/search/functions/activateSidebarToggle";
import activateFilters from "app/search/functions/activateFilters";
import renderMultiSelectFilters from "app/search/functions/renderMultiSelectFilters";

export default $scope =>
  new Promise(res => {
    let requestQueue = getRequestQueue();
    requestMultiple(requestQueue).then(reqArray => {
      requestQueue = requestQueue.map((req, i) => {
        req.data = reqArray[i];
        $scope[requestQueue[i].id] = reqArray[i];
        return req;
      });

      renderMultiSelectFilters(requestQueue);
      activateFilters();
      activateSidebarToggle();
      res();
    });
  });
