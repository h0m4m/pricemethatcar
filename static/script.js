const STORAGE_KEY = 'carsList';
let carsList = [];

function saveCarsToStorage() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(carsList));
}

function loadCarsFromStorage() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    try {
      carsList = JSON.parse(stored);
    } catch {
      carsList = [];
    }
  } else {
    carsList = [
      { make: "Chevrolet", model: "Camaro", selected: true },
      { make: "Lamborghini", model: "Aventador", selected: true }
    ];
  }
}

function renderCars() {
  const container = document.getElementById("carContainer");
  container.innerHTML = "";

  carsList.forEach((car, index) => {
    const card = document.createElement("div");
    card.className = "car-card";

    const left = document.createElement("div");
    left.className = "card-left";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = car.selected;
    checkbox.addEventListener("change", () => {
      carsList[index].selected = !carsList[index].selected;
      saveCarsToStorage();
    });

    const fields = document.createElement("div");
    fields.className = "card-fields";

    const makeInput = document.createElement("input");
    makeInput.value = car.make;
    makeInput.placeholder = "Make";
    makeInput.addEventListener("input", (e) => {
      carsList[index].make = e.target.value.trim();
      saveCarsToStorage();
    });

    const modelInput = document.createElement("input");
    modelInput.value = car.model;
    modelInput.placeholder = "Model";
    modelInput.addEventListener("input", (e) => {
      carsList[index].model = e.target.value.trim();
      saveCarsToStorage();
    });

    fields.appendChild(makeInput);
    fields.appendChild(modelInput);
    left.appendChild(checkbox);
    left.appendChild(fields);

    const actions = document.createElement("div");
    actions.className = "car-actions";

    const deleteBtn = document.createElement("button");
    deleteBtn.innerHTML = `<span class="material-icons">delete</span>`;
    deleteBtn.title = "Delete Car";
    deleteBtn.addEventListener("click", () => {
      carsList.splice(index, 1);
      saveCarsToStorage();
      renderCars();
    });

    actions.appendChild(deleteBtn);
    card.appendChild(left);
    card.appendChild(actions);
    container.appendChild(card);
  });
}

function addCar() {
  const make = document.getElementById("makeInput").value.trim();
  const model = document.getElementById("modelInput").value.trim();

  if (!make || !model) {
    alert("Both make and model are required.");
    return;
  }

  carsList.push({ make, model, selected: false });

  document.getElementById("makeInput").value = "";
  document.getElementById("modelInput").value = "";

  saveCarsToStorage();
  renderCars();
}

async function fetchPrices() {
  const selectedCars = carsList.filter((car) => car.selected);

  if (selectedCars.length === 0) {
    alert("Please select at least one car.");
    return;
  }

  const payload = {
    cars: selectedCars.map(({ make, model }) => ({ make, model }))
  };

  document.getElementById("waitMessage").style.display = "block";
  document.getElementById("formSection").style.display = "none";
  document.getElementById("controlSection").style.display = "none";
  document.getElementById("carContainer").style.display = "none";

  try {
    const res = await fetch("/scrape", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("Failed to start scraping");

    const { job_id } = await res.json();
    pollJobStatus(job_id);
  } catch (error) {
    console.error("[ERROR] Failed to start scrape:", error);
    alert("Failed to start scrape. Try again.");
    resetView();
  }
}

function pollJobStatus(jobId) {
  const poll = async () => {
    try {
      const res = await fetch(`/scrape-status/${jobId}`);
      const { status, result } = await res.json();

      if (status === "done") {
        renderResults(result);
      } else if (status === "error") {
        alert("Scrape failed.");
        resetView();
      } else {
        setTimeout(() => pollJobStatus(jobId), 2000);
      }
    } catch (e) {
      console.error("[ERROR] Polling failed:", e);
      resetView();
    }
  };
  poll();
}

function renderResults(results) {
  const container = document.getElementById("resultsSection");
  container.innerHTML = "<h2>Pricing Results</h2>";

  const carsBySignature = {};

  for (const [domain, entries] of Object.entries(results)) {
    for (const entry of entries) {
      const key = `${entry.make} ${entry.model}`;
      if (!carsBySignature[key]) {
        carsBySignature[key] = {
          make: entry.make,
          model: entry.model,
          domains: {},
          allPrices: []
        };
      }

      if (!carsBySignature[key].domains[domain]) {
        carsBySignature[key].domains[domain] = [];
      }

      entry.prices.forEach(price => {
        carsBySignature[key].domains[domain].push({ price, url: entry.url });
        if (!isNaN(parseFloat(price))) {
          carsBySignature[key].allPrices.push(parseFloat(price));
        }
      });
    }
  }

  for (const [key, data] of Object.entries(carsBySignature)) {
    const card = document.createElement("div");
    card.className = "car-card";

    const avg =
      data.allPrices.length > 0
        ? Math.round(data.allPrices.reduce((a, b) => a + b, 0) / data.allPrices.length)
        : "N/A";

    const summary = document.createElement("h3");
    summary.innerText = `${data.make} ${data.model} (${avg} AED Average, ${data.allPrices.length} prices found)`;
    card.appendChild(summary);

    for (const [domain, prices] of Object.entries(data.domains)) {
      const domainBlock = document.createElement("div");
      const domainHeader = document.createElement("strong");
      domainHeader.innerText = domain;
      domainBlock.appendChild(domainHeader);

      const ul = document.createElement("ul");
      prices.forEach(({ price, url }) => {
        const li = document.createElement("li");
        const priceText = document.createElement("span");
        priceText.textContent = `${price} AED — `;
        const a = document.createElement("a");
        a.href = url;
        a.target = "_blank";
        a.textContent = url;
        li.appendChild(priceText);
        li.appendChild(a);
        ul.appendChild(li);
      });

      domainBlock.appendChild(ul);
      card.appendChild(domainBlock);
    }

    container.appendChild(card);
  }

  document.getElementById("waitMessage").style.display = "none";
  container.style.display = "block";
}

function resetView() {
  document.getElementById("waitMessage").style.display = "none";
  document.getElementById("formSection").style.display = "flex";
  document.getElementById("controlSection").style.display = "block";
  document.getElementById("carContainer").style.display = "block";
}

window.addEventListener("DOMContentLoaded", () => {
  loadCarsFromStorage();
  document.getElementById("addCarBtn").addEventListener("click", addCar);
  document.getElementById("priceBtn").addEventListener("click", fetchPrices);
  renderCars();
});