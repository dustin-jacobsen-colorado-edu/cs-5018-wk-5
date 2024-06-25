"use strict";
window.addEventListener("load", () => {
    const reports = {};
    const addReport = function(report){
        reports[report.attr.id] = report;
        report.container = document.createElement("div");
        report.container.classList.add("report");
        let template = document.querySelector("#reports template.report").content;
        report.container.appendChild(template.cloneNode(true));
        updateReport(report);
        document.getElementById("reports").insertBefore(
            report.container,
            document.getElementById("reports").firstChild
        );
    };
    const updateReport = function(report){
        reports[report.attr.id].attr = {
            ...reports[report.attr.id].attr,
            ...report.attr
        }
        reports[report.attr.id].rel = {
            ...reports[report.attr.id].rel,
            ...report.rel
        }
        report = reports[report.attr.id];
        for(let element of report.container.querySelectorAll('[data-text]')){
            let attribute = element.getAttribute("data-text");
            if(attribute in report.attr){
                if(null === report.attr[attribute]){
                    element.textContent = "NaN";
                }else{
                    element.textContent = `${report.attr[attribute]}`;
                }
            }
        }
        for(let element of report.container.querySelectorAll('[data-show]')){
            let attribute = element.getAttribute("data-show");
            if(attribute in report.attr){
                element.style.visibility = "visible";
            }else{
                element.style.visibility = "hidden";
            }
        }
        if(report.attr.state === "PENDING"){
            setTimeout(() => {
                refresh_report(report);
            }, 5000);
        }
    };
    const refresh_report = function(report){
        const XHR = new XMLHttpRequest();
        XHR.open("GET", report.rel.self);
        XHR.addEventListener("load", (event) => {
            let response = JSON.parse(event.target.responseText);
            updateReport(response.report);
        })
        XHR.addEventListener("error", (event) => {
            setTimeout(() => {
                refresh_report(report);
            }, 60000); // longer delay to avoid spamming the server while it's struggling
        });
        XHR.send();
    }

  function sendData() {
    const XHR = new XMLHttpRequest();

    // Bind the FormData object and the form element
    const FD = new FormData(form);

    // Define what happens on successful data submission
    XHR.addEventListener("load", (event) => {
      let response = JSON.parse(event.target.responseText);
      addReport(response.report)
    });

    // Define what happens in case of error
    XHR.addEventListener("error", (event) => {
      alert("Oops! Something went wrong.");
    });

    XHR.open("POST", "/report");
    XHR.setRequestHeader("Accept", "application/json")

    // The data sent is what the user provided in the form
    XHR.send(FD);
  }

  // Get the form element
  const form = document.getElementById("filter");

  // Add 'submit' event handler
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendData();
  });
});
